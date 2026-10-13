"""Concurrency-safe work order code generation."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


def generate_work_order_code(now: datetime | None = None) -> str:
    """Generate globally unique work order code without database sequence dependencies."""

    year = (now or datetime.now(UTC)).year
    return f"WO-{year}-{uuid4().hex.upper()}"
