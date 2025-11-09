from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger("pipeline.events")


def fire_event(name: str, properties: Dict[str, Any] | None = None) -> None:
    props = properties or {}
    logger.info("event=%s props=%s", name, props)


