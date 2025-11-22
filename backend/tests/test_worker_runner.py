import asyncio
from collections import deque

import pytest

from backend.api.workers import runner


class DummyResult:
    def __init__(self, data=None, rowcount=0):
        self._data = data
        self.rowcount = rowcount

    def mappings(self):
        return self

    def first(self):
        return self._data


class DummySession:
    def __init__(self, results):
        self._results = deque(results)
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, *_args, **_kwargs):
        result = self._results.popleft()
        return result

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


class DummySessionMaker:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self._session


@pytest.mark.asyncio
async def test_claim_next_job_returns_row(monkeypatch):
    job_row = {"id": "job-1", "type": "PARSE_DOC"}
    session = DummySession(
        [
            DummyResult({"cnt": 2}),
            DummyResult(job_row),
        ]
    )
    job, queued = await runner._claim_next_job(session)  # type: ignore[attr-defined]
    assert queued == 2
    assert job == job_row
    assert session.commits == 1


@pytest.mark.asyncio
async def test_reset_stale_jobs_requeues(caplog, monkeypatch):
    session = DummySession([DummyResult(rowcount=2)])
    maker = DummySessionMaker(session)
    monkeypatch.setattr(runner, "get_sessionmaker", lambda: maker)
    await runner._reset_stale_jobs()  # type: ignore[attr-defined]
    assert session.commits == 1
    assert "reset 2 stale job(s)" in caplog.text


class FakeSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *_):
        return False


class FakeSessionFactory:
    def __call__(self):
        return FakeSessionContext()


@pytest.mark.asyncio
async def test_worker_task_processes_jobs(monkeypatch):
    jobs = deque(
        [
            ({"id": "job-123", "type": "FAKE"}, 0),
        ]
    )
    processed = []
    done = asyncio.Event()

    async def fake_claim(_session):
        if jobs:
            return jobs.popleft()
        await asyncio.sleep(0)
        return (None, 0)

    async def fake_handler(job):
        processed.append(f"handler:{job['id']}")
        done.set()

    async def fake_finish(job_id):
        processed.append(f"finish:{job_id}")

    monkeypatch.setattr(runner, "_claim_next_job", fake_claim)
    monkeypatch.setattr(runner, "_finish_job", fake_finish)
    monkeypatch.setitem(runner.HANDLERS, "FAKE", fake_handler)
    monkeypatch.setattr(runner, "get_sessionmaker", lambda: FakeSessionFactory())

    worker = asyncio.create_task(runner._worker_task(worker_id=1))  # type: ignore[attr-defined]
    await asyncio.wait_for(done.wait(), timeout=1.0)
    worker.cancel()
    with pytest.raises(asyncio.CancelledError):
        await worker

    assert processed == ["handler:job-123", "finish:job-123"]

