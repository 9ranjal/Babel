from __future__ import annotations

import asyncio
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.db import schema_table
from api.core.logging import logger
from api.core.settings import settings
from api.services.supabase_client import get_sessionmaker
from .handlers import HANDLERS


async def _claim_next_job(session: AsyncSession) -> tuple[dict[str, Any] | None, int]:
    jobs_table = schema_table("jobs")
    count_res = await session.execute(text(f"select count(*) as cnt from {jobs_table} where status = 'queued'"))
    count_row = count_res.mappings().first()
    queued_count = count_row["cnt"] if count_row else 0

    q = text(
        f"""
        with j as (
            select id
            from {jobs_table}
            where status = 'queued'
            order by created_at asc
            for update skip locked
            limit 1
        )
        update {jobs_table} as jobs
        set status = 'working', updated_at = now()
        from j
        where jobs.id = j.id
        returning jobs.*;
        """
    )
    try:
        res = await session.execute(q)
        row = res.mappings().first()
        await session.commit()
        if row:
            return dict(row), queued_count
        return None, queued_count
    except Exception:  # pragma: no cover - let caller handle logging
        await session.rollback()
        raise


async def _finish_job(job_id: str) -> None:
    S = get_sessionmaker()
    async with S() as session:
        await session.execute(
            text(f"update {schema_table('jobs')} set status='done', updated_at = now() where id = :id"),
            {"id": job_id},
        )
        await session.commit()


async def _fail_job(job: dict[str, Any], error: str) -> None:
    attempts = int(job.get("attempts", 0)) + 1
    logger.warning(
        "worker job failure id=%s type=%s attempts=%s err=%s",
        job.get("id"),
        job.get("type"),
        attempts,
        error,
    )
    S = get_sessionmaker()
    async with S() as session:
        err_trimmed = (error or "")[:2000]
        if attempts >= 3:
            await session.execute(
                text(
                    f"""
                    update {schema_table('jobs')}
                    set status='failed', attempts=:attempts, last_error=:err, failed_at=now(), updated_at=now()
                    where id = :id
                    """
                ),
                {"id": job["id"], "attempts": attempts, "err": err_trimmed},
            )
        else:
            delay = min(8.0, 2.0 ** attempts)
            await asyncio.sleep(delay)
            await session.execute(
                text(
                    f"""
                    update {schema_table('jobs')}
                    set status='queued', attempts=:attempts, last_error=:err, updated_at=now()
                    where id = :id
                    """
                ),
                {"id": job["id"], "attempts": attempts, "err": err_trimmed},
            )
        await session.commit()


async def _reset_stale_jobs() -> None:
    S = get_sessionmaker()
    async with S() as session:
        jobs_table = schema_table("jobs")
        res = await session.execute(
            text(
                f"""
                update {jobs_table}
                set status='queued',
                    attempts = attempts + 1,
                    last_error = coalesce(last_error, '') || ' [reset-stale]',
                    updated_at = now()
                where status = 'working'
                  and updated_at < now() - (:seconds * interval '1 second')
                """
            ),
            {"seconds": settings.WORKER_STALE_JOB_SECONDS},
        )
        if res.rowcount:
            logger.warning("reset %d stale job(s) back to queued", res.rowcount)
        await session.commit()


async def _stale_job_reaper() -> None:
    interval = max(5, settings.WORKER_STALE_CHECK_INTERVAL_SECONDS)
    try:
        while True:
            try:
                await _reset_stale_jobs()
            except Exception:
                logger.exception("failed to reset stale jobs")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("stale job reaper cancelled")
        raise


async def _worker_task(worker_id: int) -> None:
    poll_seconds = max(0.05, settings.JOB_POLL_INTERVAL_MS / 1000.0)
    idle_since: Optional[float] = None
    loop = asyncio.get_running_loop()
    SessionLocal = get_sessionmaker()
    try:
        while True:
            async with SessionLocal() as session:
                try:
                    job, queued_count = await _claim_next_job(session)
                except Exception as exc:
                    logger.error("worker[%d] database error during claim: %s", worker_id, exc, exc_info=True)
                    await asyncio.sleep(poll_seconds)
                    continue
            if not job:
                now = loop.time()
                if queued_count > 0:
                    logger.warning(
                        "worker[%d] found %d queued jobs but couldn't claim any (may be locked by another worker)",
                        worker_id,
                        queued_count,
                    )
                if idle_since is None:
                    idle_since = now
                elif now - idle_since >= settings.WORKER_STALE_SECONDS:
                    logger.warning("worker[%d] idle for %.1fs (no queued jobs found)", worker_id, now - idle_since)
                    idle_since = now
                await asyncio.sleep(poll_seconds)
                continue
            idle_since = None
            job_type = job.get("type")
            logger.info("worker[%d] claimed job id=%s type=%s", worker_id, job.get("id"), job_type)
            handler = HANDLERS.get(job_type)
            if not handler:
                logger.error("worker[%d] handler missing for type=%s id=%s", worker_id, job_type, job.get("id"))
                await _fail_job(job, f"no handler for type={job_type}")
                continue
            try:
                await handler(job)
                await _finish_job(job["id"])
                logger.info("worker[%d] finished job id=%s type=%s", worker_id, job.get("id"), job_type)
            except asyncio.CancelledError:
                logger.info("worker[%d] cancelled during handler", worker_id)
                raise
            except Exception as exc:  # pragma: no cover
                logger.exception("worker[%d] handler error type=%s id=%s", worker_id, job_type, job.get("id"))
                await _fail_job(job, str(exc))
    except asyncio.CancelledError:
        logger.info("worker[%d] cancelled", worker_id)
        raise


async def run_worker_loop() -> None:
    worker_count = max(1, settings.WORKER_PARALLELISM)
    logger.info("starting %d worker(s) poll=%.2fs", worker_count, max(0.05, settings.JOB_POLL_INTERVAL_MS / 1000.0))
    worker_tasks = [asyncio.create_task(_worker_task(i + 1)) for i in range(worker_count)]
    reaper_task = asyncio.create_task(_stale_job_reaper())
    try:
        await asyncio.gather(*worker_tasks, reaper_task)
    except asyncio.CancelledError:
        logger.info("worker loop cancelled, shutting down workers")
        for task in worker_tasks + [reaper_task]:
            task.cancel()
        await asyncio.gather(*worker_tasks, reaper_task, return_exceptions=True)
        raise


def main() -> None:
    asyncio.run(run_worker_loop())


if __name__ == "__main__":
    main()


