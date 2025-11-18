from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.logging import logger
from api.core.settings import settings
from api.services.supabase_client import get_sessionmaker
from .handlers import HANDLERS


async def _claim_next_job(session: AsyncSession) -> dict | None:
    # First check how many queued jobs exist (for debugging)
    count_res = await session.execute(text("select count(*) as cnt from public.jobs where status = 'queued'"))
    count_row = count_res.mappings().first()
    queued_count = count_row["cnt"] if count_row else 0
    if queued_count > 0:
        logger.info("worker found %d queued job(s), attempting to claim", queued_count)
    
    q = text(
        """
        with j as (
            select id
            from public.jobs
            where status = 'queued'
            order by created_at asc
            for update skip locked
            limit 1
        )
        update public.jobs as jobs
        set status = 'working', updated_at = now()
        from j
        where jobs.id = j.id
        returning jobs.*;
        """
    )
    res = await session.execute(q)
    row = res.mappings().first()
    if row:
        return dict(row)
    elif queued_count > 0:
        logger.warning("worker found %d queued jobs but couldn't claim any (may be locked by another worker)", queued_count)
    return None


async def _finish_job(session: AsyncSession, job_id: str) -> None:
    await session.execute(
        text("update public.jobs set status='done', updated_at = now() where id = :id"),
        {"id": job_id},
    )


async def _fail_job(session: AsyncSession, job: dict, error: str) -> None:
    attempts = int(job.get("attempts", 0)) + 1
    logger.warning(
        "worker job failure id=%s type=%s attempts=%s err=%s",
        job.get("id"),
        job.get("type"),
        attempts,
        error,
    )
    if attempts >= 3:
        await session.execute(
            text(
                """
                update public.jobs
                set status='failed', attempts=:attempts, last_error=:err, failed_at=now(), updated_at=now()
                where id = :id
                """
            ),
            {"id": job["id"], "attempts": attempts, "err": error[:2000]},
        )
        return
    # exponential backoff: simple sleep prior to requeue (dev-only)
    delay = min(8.0, 2.0 ** attempts)
    await asyncio.sleep(delay)
    await session.execute(
        text(
            """
            update public.jobs
            set status='queued', attempts=:attempts, last_error=:err, updated_at=now()
            where id = :id
            """
        ),
        {"id": job["id"], "attempts": attempts, "err": error[:2000]},
    )


async def run_worker_loop() -> None:
    S = get_sessionmaker()
    poll_seconds = max(0.05, settings.JOB_POLL_INTERVAL_MS / 1000.0)
    logger.info("worker loop starting poll=%.2fs", poll_seconds)
    idle_since: Optional[float] = None
    loop = asyncio.get_running_loop()
    try:
        while True:
            async with S() as session:
                try:
                    job = await _claim_next_job(session)
                except Exception as exc:
                    logger.error("worker database error during job claim: %s", exc, exc_info=True)
                    await session.rollback()
                    await asyncio.sleep(poll_seconds)
                    continue
                
                if not job:
                    await session.commit()
                    now = loop.time()
                    if idle_since is None:
                        idle_since = now
                    elif now - idle_since >= settings.WORKER_STALE_SECONDS:
                        logger.warning("worker idle for %.1fs (no queued jobs found)", now - idle_since)
                        idle_since = now
                    await asyncio.sleep(poll_seconds)
                    continue
                idle_since = None
                job_type = job.get("type")
                logger.info("worker claimed job id=%s type=%s", job.get("id"), job_type)
                handler = HANDLERS.get(job_type)
                if not handler:
                    logger.error("worker handler missing for type=%s id=%s", job_type, job.get("id"))
                    await _fail_job(session, job, f"no handler for type={job_type}")
                    await session.commit()
                    continue
                try:
                    await handler(job)
                    await _finish_job(session, job["id"])
                    logger.info("worker finished job id=%s type=%s", job.get("id"), job_type)
                except Exception as exc:  # pragma: no cover
                    logger.exception("worker handler error type=%s id=%s", job_type, job.get("id"))
                    await _fail_job(session, job, str(exc))
                await session.commit()
    except asyncio.CancelledError:  # pragma: no cover
        logger.info("worker loop cancelled")
        raise


def main() -> None:
    asyncio.run(run_worker_loop())


if __name__ == "__main__":
    main()


