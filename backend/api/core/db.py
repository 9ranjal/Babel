from __future__ import annotations

from api.core.settings import settings


def schema_table(table_name: str) -> str:
    schema = (settings.DB_SCHEMA or "").strip()
    return f"{schema}.{table_name}" if schema else table_name


