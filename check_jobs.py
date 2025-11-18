#!/usr/bin/env python3
"""Quick script to check for queued jobs in the database"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import text
from api.services.supabase_client import get_sessionmaker
from api.core.logging import logger

async def check_jobs():
    S = get_sessionmaker()
    async with S() as session:
        # Check all job statuses
        result = await session.execute(
            text("""
                select status, count(*) as cnt
                from public.jobs
                group by status
                order by status
            """)
        )
        status_counts = result.mappings().all()
        
        print("\n📊 Job Status Summary:")
        print("-" * 40)
        for row in status_counts:
            print(f"  {row['status']}: {row['cnt']}")
        
        # Check recent jobs
        recent = await session.execute(
            text("""
                select id, type, status, document_id, created_at, updated_at
                from public.jobs
                order by created_at desc
                limit 10
            """)
        )
        recent_jobs = recent.mappings().all()
        
        print("\n📋 Recent Jobs (last 10):")
        print("-" * 40)
        for job in recent_jobs:
            job_id = str(job['id'])[:8] if job['id'] else 'N/A'
            doc_id = str(job['document_id'])[:8] if job['document_id'] else 'N/A'
            print(f"  ID: {job_id}... | Type: {job['type']} | Status: {job['status']} | Doc: {doc_id}")
            print(f"    Created: {job['created_at']} | Updated: {job['updated_at']}")
        
        # Check queued jobs specifically
        queued = await session.execute(
            text("""
                select id, type, document_id, created_at
                from public.jobs
                where status = 'queued'
                order by created_at asc
            """)
        )
        queued_jobs = queued.mappings().all()
        
        print(f"\n⏳ Queued Jobs ({len(queued_jobs)}):")
        print("-" * 40)
        if queued_jobs:
            for job in queued_jobs:
                job_id = str(job['id'])[:8] if job['id'] else 'N/A'
                doc_id = str(job['document_id'])[:8] if job['document_id'] else 'N/A'
                print(f"  ID: {job_id}... | Type: {job['type']} | Doc: {doc_id} | Created: {job['created_at']}")
        else:
            print("  No queued jobs found")
        
        # Check documents that might need processing
        docs = await session.execute(
            text("""
                select id, filename, status, created_at
                from public.documents
                order by created_at desc
                limit 5
            """)
        )
        recent_docs = docs.mappings().all()
        
        print(f"\n📄 Recent Documents (last 5):")
        print("-" * 40)
        for doc in recent_docs:
            doc_id = str(doc['id'])[:8] if doc['id'] else 'N/A'
            print(f"  ID: {doc_id}... | File: {doc['filename']} | Status: {doc['status']} | Created: {doc['created_at']}")
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(check_jobs())

