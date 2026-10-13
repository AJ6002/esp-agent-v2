"""Optional OpenTelemetry integration (disabled by default).

Principles:

- ``OTEL_ENABLED=false`` (default): Zero dependency path -- ``industrial_span`` returns no-op context;
- ``OTEL_ENABLED=true``: Initializes TracerProvider + OTLP HTTP Exporter;
  Logs warning and continues if Collector is unreachable, never breaking industrial pipeline;
- Sample rate controlled by ``OTEL_TRACE_SAMPLE_RATE`` (0.0~1.0).
"""

from __future__ import annotations

import contextlib
import functools
import logging
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from app.core.config import settings

logger = logging.getLogger("app.observability")

_state_lock = threading.Lock()
_tracer: Any | None = None
_initialised = False


def _initialise() -> Any | None:
    """Lazy load and initialize OTel TracerProvider; degrades to None on failure."""
    global _tracer, _initialised
    with _state_lock:
        if _initialised:
            return _tracer
        _initialised = True
        if not settings.OTEL_ENABLED:
            return None
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.trace.sampling import (
                ParentBased,
                TraceIdRatioBased,
            )

            resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
            provider = TracerProvider(
                resource=resource,
                sampler=ParentBased(
                    TraceIdRatioBased(
                        max(0.0, min(settings.OTEL_TRACE_SAMPLE_RATE, 1.0))
                    )
                ),
            )
            endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
            exporter = (
                OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            _tracer = trace.get_tracer("app.industrial")
            logger.info(
                "OpenTelemetry enabled (service=%s endpoint=%s sample=%.2f)",
                settings.OTEL_SERVICE_NAME,
                endpoint or "(default)",
                settings.OTEL_TRACE_SAMPLE_RATE,
            )
        except Exception as exc:
            logger.warning("OpenTelemetry init failed; continuing without: %s", exc)
            _tracer = None
        return _tracer


@contextmanager
def industrial_span(
    name: str, attributes: dict[str, Any] | None = None
) -> Iterator[Any]:
    """Span context for critical industrial stages; zero-overhead no-op when disabled.

    All OTel exceptions degrade to no-op -- observability never blocks business logic.
    """
    tracer = _initialise() if settings.OTEL_ENABLED else None
    if tracer is None:
        yield None
        return
    try:
        with tracer.start_as_current_span(name) as span:
            for key, value in (attributes or {}).items():
                if value is not None:
                    # Attribute failure does not affect pipeline (observability degradation).
                    with contextlib.suppress(Exception):
                        span.set_attribute(key, value)
            yield span
    except Exception as exc:
        logger.warning("span %s failed: %s", name, exc)
        yield None


def traced_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Function-level span decorator (synchronous).

    Covers critical industrial stages with zero boilerplate; attributes is static dict.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with industrial_span(name, attributes):
                return func(*args, **kwargs)

        return wrapper

    return decorator
