"""Industrial event trace context (Trace Context).

Design goals:

- A complete industrial event chain (OPC UA DataChange -> Telemetry -> Anomaly ->
  Prediction -> Alarm -> WorkOrder -> Verification) shares a single ``trace_id``;
- Built on :mod:`contextvars`: async-safe, request-safe, and background-task-safe;
- Ingress rules:
  * Existing trace context -> reused;
  * New event ingress (gateway sync / subscription flush / manual telemetry) -> generates new trace_id;
  * Alarm analysis -> inherits alarm trace_id.

Zero external dependencies; OTel integration is an optional bypass.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import uuid4

logger = logging.getLogger("app.observability")

TRACE_ID_LENGTH = 36


def new_trace_id() -> str:
    """Generate new trace_id (UUID4 string)."""
    return str(uuid4())


@dataclass(frozen=True, slots=True)
class TraceContext:
    """Trace context for an industrial event chain."""

    trace_id: str
    request_id: str | None = None
    source: str = "unknown"


_context: ContextVar[TraceContext | None] = ContextVar(
    "industrial_trace_context", default=None
)

# HTTP request_id and industrial trace_id semantics are strictly decoupled:
# former identifies single HTTP request, latter identifies cross-system industrial event chain.
_request_id_var: ContextVar[str | None] = ContextVar("http_request_id", default=None)


def current_request_id() -> str | None:
    """Current HTTP request_id (set by request middleware)."""
    return _request_id_var.get()


def set_request_id(value: str) -> object:
    """Set request_id for current request, returning token for restoration."""
    return _request_id_var.set(value)


def reset_request_id(token: object) -> None:
    """Restore request_id context."""
    _request_id_var.reset(token)  # type: ignore[arg-type]


def current_context() -> TraceContext | None:
    """Return current context (None if absent). Read-only, does not create."""
    return _context.get()


def current_trace_id() -> str | None:
    """Current trace_id; None when outside active trace."""
    ctx = _context.get()
    return ctx.trace_id if ctx else None


def start_trace(source: str, *, request_id: str | None = None) -> TraceContext:
    """Generate and bind new trace_id for industrial event ingress.

    Invoked at ingress points only (gateway sync cycle, subscription flush, manual telemetry ingestion).
    """
    ctx = TraceContext(trace_id=new_trace_id(), request_id=request_id, source=source)
    _context.set(ctx)
    return ctx


def bind_trace(trace_id: str | None, *, source: str) -> TraceContext:
    """Bind existing trace_id (e.g. inheriting from alarm trace).

    Generates fallback id with warning if empty -- callers should explicitly specify ingress semantics.
    """
    if not trace_id:
        logger.warning(
            "bind_trace called without trace_id (source=%s); generating new",
            source,
        )
        return start_trace(source)
    ctx = TraceContext(trace_id=str(trace_id), source=source)
    _context.set(ctx)
    return ctx


def reset_context(token: object) -> None:
    """Restore context using token returned by ``ContextVar.set`` (testing)."""
    # ContextVar.reset requires token type; narrowed to Any to keep API clean.
    _context.reset(token)  # type: ignore[arg-type]


def trace_attributes(**extra: object) -> dict[str, object]:
    """Common log/span attribute assembly: automatically attaches current trace_id."""
    attrs: dict[str, object] = {}
    ctx = _context.get()
    if ctx:
        attrs["trace_id"] = ctx.trace_id
        if ctx.request_id:
            attrs["request_id"] = ctx.request_id
        attrs["trace_source"] = ctx.source
    attrs.update(extra)
    return attrs


class TraceLogFilter(logging.Filter):
    """Inject current trace_id / request_id into log records.

    Placeholders with "-" when outside context, maintaining stable log formatting.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = current_trace_id() or "-"
        record.request_id = current_request_id() or "-"
        return True
