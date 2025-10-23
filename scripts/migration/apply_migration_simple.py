#!/usr/bin/env python3
"""
Apply transactions migration via direct SQL execution
"""
import os
import sys

# Set environment variables for the migration
os.environ['SUPABASE_URL'] = 'http://localhost:54321'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'
os.environ['OPENROUTER_API_KEY'] = 'dummy'

sys.path.append('backend')

from backend.api.services.supabase import get_supabase_client

def apply_migration():
    """Apply the transactions migration"""
    supabase = get_supabase_client()
    
    # Read the migration file
    with open('supabase/migrations/005_transactions.sql', 'r') as f:
        migration_sql = f.read()
    
    # Split into individual statements
    statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
    
    print(f"Applying {len(statements)} SQL statements...")
    
    for i, statement in enumerate(statements):
        if not statement or statement.startswith('--'):
            continue
        try:
            print(f"Executing statement {i+1}...")
            # Use raw SQL execution
            result = supabase.postgrest.rpc('exec_sql', {'sql': statement}).execute()
            print(f"✅ Statement {i+1} executed successfully")
        except Exception as e:
            print(f"❌ Error in statement {i+1}: {e}")
            print(f"Statement: {statement[:100]}...")
            # Continue with other statements
    
    print("Migration completed!")

if __name__ == "__main__":
    apply_migration()
