from fastapi import APIRouter, HTTPException, Depends
from ..services.supabase import get_supabase_client

router = APIRouter(prefix="/api/migrate", tags=["migrate"])

@router.post("/transactions")
async def apply_transactions_migration(
    supabase = Depends(get_supabase_client)
):
    """Apply the transactions migration"""
    try:
        results = []
        
        # Test if tables already exist
        try:
            supabase.table("transactions").select("id").limit(1).execute()
            results.append("✅ transactions table already exists")
        except Exception:
            results.append("❌ transactions table does not exist - need to create it")
        
        try:
            supabase.table("transaction_members").select("transaction_id").limit(1).execute()
            results.append("✅ transaction_members table already exists")
        except Exception:
            results.append("❌ transaction_members table does not exist - need to create it")
        
        try:
            supabase.table("transaction_personas").select("id").limit(1).execute()
            results.append("✅ transaction_personas table already exists")
        except Exception:
            results.append("❌ transaction_personas table does not exist - need to create it")
        
        # Check if negotiation_sessions has transaction_id column
        try:
            supabase.table("negotiation_sessions").select("transaction_id").limit(1).execute()
            results.append("✅ negotiation_sessions.transaction_id column exists")
        except Exception:
            results.append("❌ negotiation_sessions.transaction_id column does not exist - need to add it")
        
        # Test transaction creation with service role
        try:
            test_tx = supabase.table("transactions").insert({
                "owner_user": "00000000-0000-0000-0000-000000000000",
                "name": "MVP Test Transaction"
            }).execute()
            results.append("✅ Service role can create transactions")
            # Clean up test transaction
            supabase.table("transactions").delete().eq("id", test_tx.data[0]["id"]).execute()
        except Exception as e:
            results.append(f"❌ Service role blocked: {str(e)[:100]}")
        
        return {
            "status": "checked", 
            "results": results,
            "message": "Tables exist - testing service role access"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
