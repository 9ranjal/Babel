#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set up environment
os.environ.setdefault("SUPABASE_DB_URL", "")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "")
os.environ.setdefault("OPENROUTER_API_KEY", "")
os.environ.setdefault("DEMO_USER_ID", "00000000-0000-0000-0000-000000000001")

try:
    from api.core.settings import settings
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

    async def check_doc():
        try:
            engine = create_async_engine(settings.SUPABASE_DB_URL)
            async with AsyncSession(engine) as session:
                # Check the document status
                result = await session.execute(text('SELECT id, status, graph_json, filename FROM public.documents WHERE id = \'ae0afe13-149a-4695-931b-071daa52682e\''))
                doc = result.mappings().first()
                if doc:
                    print('Document status:', doc['status'])
                    print('Has graph_json:', doc['graph_json'] is not None)
                    if doc['graph_json']:
                        import json
                        graph = json.loads(doc['graph_json'])
                        print('Graph nodes:', len(graph.get('nodes', [])))
                        print('Graph edges:', len(graph.get('edges', [])))
                        print('Graph content preview:', str(graph)[:200])
                    print('Filename:', doc['filename'])
                else:
                    print('Document not found')

                # Check for clauses
                result = await session.execute(text('SELECT count(*) FROM public.clauses WHERE document_id = \'ae0afe13-149a-4695-931b-071daa52682e\''))
                clause_count = result.scalar()
                print('Clause count:', clause_count)

                # Check for jobs
                result = await session.execute(text('SELECT type, status, created_at FROM public.jobs WHERE document_id = \'ae0afe13-149a-4695-931b-071daa52682e\' ORDER BY created_at DESC'))
                jobs = result.mappings().all()
                print('Jobs:')
                for job in jobs:
                    print(f'  {job["type"]}: {job["status"]} ({job["created_at"]})')

        except Exception as e:
            print(f"Error checking document: {e}")

    asyncio.run(check_doc())

except Exception as e:
    print(f"Import error: {e}")
