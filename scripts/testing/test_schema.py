#!/usr/bin/env python3
"""
Test the Supabase schema to confirm all tables exist
"""
import os
import sys

# Set environment variables
os.environ['SUPABASE_URL'] = 'http://localhost:54321'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'
os.environ['OPENROUTER_API_KEY'] = 'dummy'

sys.path.append('backend')

from backend.api.services.supabase import get_supabase_client

def test_schema():
    """Test the schema structure"""
    supabase = get_supabase_client()
    
    print("🔍 Testing Supabase Schema...")
    
    # Test each table
    tables_to_test = [
        ("transactions", ["id", "owner_user", "name", "created_at"]),
        ("transaction_members", ["transaction_id", "user_id", "role", "added_at"]),
        ("transaction_personas", ["id", "transaction_id", "kind", "label", "persona_id", "created_at"]),
        ("negotiation_sessions", ["id", "transaction_id", "company_persona", "investor_persona", "regime", "created_at"]),
        ("personas", ["id", "owner_user", "kind", "attrs", "leverage_score", "weights", "batna", "created_at"]),
        ("users", ["user_id", "email", "created_at"])
    ]
    
    results = {}
    
    for table_name, expected_columns in tables_to_test:
        try:
            # Try to select from the table
            result = supabase.table(table_name).select("*").limit(1).execute()
            results[table_name] = {
                "exists": True,
                "accessible": True,
                "columns": list(result.data[0].keys()) if result.data else []
            }
            print(f"✅ {table_name}: exists and accessible")
        except Exception as e:
            if "does not exist" in str(e):
                results[table_name] = {"exists": False, "accessible": False, "error": str(e)}
                print(f"❌ {table_name}: table does not exist")
            else:
                results[table_name] = {"exists": True, "accessible": False, "error": str(e)}
                print(f"⚠️  {table_name}: exists but not accessible - {str(e)[:100]}")
    
    # Test RLS policies
    print("\n🔒 Testing RLS Policies...")
    
    # Test if we can insert with service role
    try:
        test_tx = supabase.table("transactions").insert({
            "owner_user": "00000000-0000-0000-0000-000000000000",
            "name": "Test Transaction"
        }).execute()
        print("✅ RLS allows service role inserts")
    except Exception as e:
        print(f"❌ RLS blocks service role inserts: {str(e)[:100]}")
    
    return results

if __name__ == "__main__":
    results = test_schema()
    print(f"\n📊 Schema Test Results:")
    for table, result in results.items():
        status = "✅" if result.get("exists") and result.get("accessible") else "❌"
        print(f"{status} {table}: {result}")
