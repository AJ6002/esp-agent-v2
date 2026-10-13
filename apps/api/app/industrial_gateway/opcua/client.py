"""OPC UA Client abstraction and implementations.

Security constraints (industrial control security requirements):

- Gateway is **read-only**: The ``OpcUaClient`` protocol does not define any write methods;
- ``AsyncuaOpcUaClient`` only calls ``read_data_value`` and does not hold writable handles;
- Both implementations explicitly provide ``write_node`` and immediately raise :class:`PermissionError`,
  serving as a code-level defense line for "read-only mode"; any future write operation must first pass
  the platform Human Approval (OperationApproval) workflow and cannot bypass it.

``asyncua`` is an optional dependency: only lazily imported in ``opcua`` mode;
Mock mode (no physical PLC / asyncua not installed) uses in-process :class:`MockOpcUaClient`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.industrial_gateway.opcua.models import (
    QUALITY_GOOD,
    NodeRead,
    quality_from_status_code,
)

if TYPE_CHECKING:  # pragma: no cover - required for type checking only
    from collections.abc import Callable

    # value_provider(node_id) -> (value, source_timestamp)
    ValueProvider = Callable[
        [str], tuple[float | bool | int | str | None, datetime | None]
    ]

READ_ONLY_MODE = "read-only"

_WRITE_REJECTED_MESSAGE = (
    "OPC UA Gateway is in read-only mode: PLC write prohibited. "
    "Write operations must go through the independent Human Approval workflow."
)


@runtime_checkable
class OpcUaClient(Protocol):
    """OPC UA client minimal protocol (read-only)."""

    endpoint: str

    @property
    def connected(self) -> bool: ...

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    async def read_node(self, node_id: str) -> NodeRead: ...


def _coerce_value(raw: Any) -> float | bool | int | str | None:
    """Normalize OPC UA DataValue into a platform scalar."""
    if raw is None or isinstance(raw, bool | int | float | str):
        return raw
    if isinstance(raw, bytes):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class AsyncuaOpcUaClient:
    """Real OPC UA client based on ``asyncua`` (read-only).

    Used to connect to software simulators or on-site OPC UA Server / PLC interfaces.
    """

    def __init__(self, endpoint: str, *, timeout_seconds: float = 4.0) -> None:
        self.endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._client: Any | None = None

    @property
    def connected(self) -> bool:
        return self._client is not None

    async def connect(self) -> None:
        from asyncua import Client  # Lazy import: asyncua not needed in mock mode

        client = Client(self.endpoint, timeout=self._timeout_seconds)
        await client.connect()
        self._client = client

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    async def read_node(self, node_id: str) -> NodeRead:
        if self._client is None:
            raise ConnectionError("OPC UA client is not connected")
        node = self._client.get_node(node_id)
        data_value = await node.read_data_value()
        variant = getattr(data_value, "Value", None)
        raw_value = getattr(variant, "Value", None) if variant is not None else None
        status = getattr(data_value, "StatusCode", None)
        status_code = getattr(status, "value", None) if status is not None else None
        quality = quality_from_status_code(status_code)
        return NodeRead(
            node_id=node_id,
            value=_coerce_value(raw_value),
            source_timestamp=_as_utc(getattr(data_value, "SourceTimestamp", None)),
            status_code=status_code,
            quality=quality,
        )

    async def write_node(self, node_id: str, value: Any) -> None:
        """Explicitly reject write: gateway is read-only, see module docstring."""
        raise PermissionError(_WRITE_REJECTED_MESSAGE)


class MockOpcUaClient:
    """In-process OPC UA mock client.

    Opens no network connections and does not require ``asyncua``: reads deterministic
    values from an injected ``value_provider`` (typically from ``simulator.generator.MotorSimulator``),
    used for complete demo and unit tests without physical PLCs.
    """

    def __init__(
        self,
        endpoint: str = "mock://opcua-simulator",
        *,
        value_provider: ValueProvider | None = None,
    ) -> None:
        self.endpoint = endpoint
        self._value_provider = value_provider
        self._connected = False
        self._available = True

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def available(self) -> bool:
        return self._available

    def set_value_provider(self, provider: ValueProvider) -> None:
        self._value_provider = provider

    def set_available(self, available: bool) -> None:
        """Inject connection fault for gateway fallback testing."""
        self._available = available
        if not available:
            self._connected = False

    async def connect(self) -> None:
        if not self._available:
            raise ConnectionError(f"Simulated OPC UA Server unreachable: {self.endpoint}")
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def read_node(self, node_id: str) -> NodeRead:
        if not self._connected:
            raise ConnectionError("OPC UA client is not connected")
        if self._value_provider is None:
            raise ValueError("MockOpcUaClient value_provider is not configured")
        value, timestamp = self._value_provider(node_id)
        return NodeRead(
            node_id=node_id,
            value=value,
            source_timestamp=_as_utc(timestamp),
            status_code=None,
            quality=QUALITY_GOOD,
        )

    async def write_node(self, node_id: str, value: Any) -> None:
        """Explicitly reject write: gateway is read-only, see module docstring."""
        raise PermissionError(_WRITE_REJECTED_MESSAGE)
