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
    from api.core.logging import logger
    from urllib.parse import urlparse
    
    global _engine
    if _engine is None:
        db_url = _supabase_db_url()
        # Log connection details (redact password)
        parsed = urlparse(db_url)
        safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port or 5432}{parsed.path}"
        logger.info("Initializing database engine: host=%s port=%s db=%s", parsed.hostname, parsed.port or 5432, parsed.path or "/postgres")
        try:
            _engine = create_async_engine(db_url, pool_pre_ping=True, echo=False)
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error("Failed to create database engine: %s", e, exc_info=True)
            raise
    return _engine


def get_sessionmaker() -> sessionmaker:
    from api.core.logging import logger
    
    global _session_maker
    if _session_maker is None:
        logger.info("Creating database session maker")
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
    from api.core.logging import logger
    
    supabase_url = _supabase_url()
    service_role_key = _service_role_key()
    url = f"{supabase_url}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
        "Content-Type": content_type,
    }
    logger.info("upload_file: bucket=%s path=%s url=%s content_len=%d", bucket, path, url, len(bytes_content))
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(url, headers=headers, content=bytes_content)
        if resp.status_code not in (200, 201):
            error_detail = resp.text
            error_json = None
            try:
                error_json = resp.json()
            except Exception:
                pass
            logger.error(
                "Supabase Storage upload failed: status=%d bucket=%s path=%s error=%s json=%s",
                resp.status_code,
                bucket,
                path,
                error_detail[:500],
                error_json,
            )
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


