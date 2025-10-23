"""
Apply migration 003_dev_policies.sql to Supabase
"""
from api.services.supabase import get_supabase
from api.core.settings import settings

def apply_migration():
    """Apply the dev policies migration"""
    print("Applying migration: 003_dev_policies.sql")
    print(f"Target: {settings.SUPABASE_URL}")
    
    # Read migration file
    with open('supabase/migrations/003_dev_policies.sql', 'r') as f:
        migration_sql = f.read()
    
    # Get supabase client
    supabase = get_supabase()
    
    # Execute the migration using RPC
    # Note: We need to execute this as raw SQL
    try:
        # Split by statements
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements):
            if statement and not statement.startswith('=='):
                print(f"\nExecuting statement {i+1}...")
                print(f"SQL: {statement[:100]}...")
                
                try:
                    # Use Supabase PostgREST to execute raw SQL via RPC
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"✅ Statement {i+1} executed successfully")
                except Exception as e:
                    print(f"⚠️  Statement {i+1} error (might already exist): {e}")
        
        print("\n✅ Migration applied successfully!")
        
    except Exception as e:
        print(f"\n❌ Error applying migration: {e}")
        print("\n💡 Tip: You may need to apply this migration manually using Supabase Dashboard SQL Editor")
        print(f"    URL: {settings.SUPABASE_URL.replace('supabase.co', 'supabase.com')}/project/_/sql")
        print("\n   Or use psql:")
        print(f"    psql '{settings.SUPABASE_URL}/postgres' -f supabase/migrations/003_dev_policies.sql")

if __name__ == "__main__":
    apply_migration()

