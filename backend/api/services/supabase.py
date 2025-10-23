# api/services/supabase.py
from supabase import create_client, Client
from api.core.settings import settings

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _supabase

# Alias for FastAPI dependency injection
def get_supabase_client() -> Client:
    """
    FastAPI dependency for Supabase client
    
    Usage in routes:
        @router.get("/endpoint")
        def endpoint(supabase = Depends(get_supabase_client)):
            ...
    """
    return get_supabase()

