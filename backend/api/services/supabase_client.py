import os
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.core.settings import settings

_engine: Optional[AsyncEngine] = None
_session_maker: Optional[sessionmaker] = None


def _require(value: Optional[str], name: str) -> str:
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


def _supabase_db_url() -> str:
    raw = _require(os.getenv("SUPABASE_DB_URL") or settings.SUPABASE_DB_URL, "SUPABASE_DB_URL")
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw


def _supabase_url() -> str:
    return _require(os.getenv("SUPABASE_URL") or settings.SUPABASE_URL, "SUPABASE_URL")


def _service_role_key() -> str:
    return _require(
        os.getenv("SUPABASE_SERVICE_ROLE_KEY") or settings.SUPABASE_SERVICE_ROLE_KEY,
        "SUPABASE_SERVICE_ROLE_KEY",
    )


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(_supabase_db_url(), pool_pre_ping=True)
    return _engine


def get_sessionmaker() -> sessionmaker:
    global _session_maker
    if _session_maker is None:
        _session_maker = sessionmaker(bind=get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _session_maker


async def create_signed_url(bucket: str, path: str, expires_in: int = 3600) -> str:
    supabase_url = _supabase_url()
    service_role_key = _service_role_key()
    url = f"{supabase_url}/storage/v1/object/sign/{bucket}/{path}?expiresIn={expires_in}"
    headers = {"Authorization": f"Bearer {service_role_key}", "apikey": service_role_key}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return f"{supabase_url}{data['signedURL']}"


async def upload_file(bucket: str, path: str, bytes_content: bytes, content_type: str) -> None:
    supabase_url = _supabase_url()
    service_role_key = _service_role_key()
    url = f"{supabase_url}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
        "Content-Type": content_type,
    }
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(url, headers=headers, content=bytes_content)
        if resp.status_code not in (200, 201):
            error_detail = resp.text
            print(f"Supabase Storage Error: {resp.status_code} - {error_detail}")
            resp.raise_for_status()


async def download_file(bucket: str, path: str) -> bytes:
    supabase_url = _supabase_url()
    service_role_key = _service_role_key()
    url = f"{supabase_url}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
    }
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.content


