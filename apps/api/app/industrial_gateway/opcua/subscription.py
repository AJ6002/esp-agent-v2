"""OPC UA Subscription abstraction (event-driven, read-only).

Design principles:

- **Decoupled from asyncua**: protocol + two implementations (Asyncua / Mock);
- **Read-only**: subscriptions receive DataChange notifications only, no write paths exist;
- Coexists with polling: the polling client in ``client.py`` remains intact;
  subscriptions act as an additional parallel trigger source, sharing downstream quality and AI pipelines.

Event callbacks are synchronous functions (asyncua handler semantics); implementations perform memory buffering only,
with all IO (database ingestion/alarms) executed by the service flush loop.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.industrial_gateway.opcua.models import (
    NodeRead,
    quality_from_status_code,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence

SUBSCRIPTION_STATUS_STOPPED = "stopped"
SUBSCRIPTION_STATUS_ACTIVE = "active"
SUBSCRIPTION_STATUS_ERROR = "error"

WRITE_REJECTED_MESSAGE = (
    "OPC UA Subscription operates in read-only mode: subscriptions can only read DataChange notifications, "
    "not write to PLCs. Any future control operations must undergo the OperationApproval workflow."
)

# Callback signature: synchronous function; blocking IO in callback is prohibited.
DataChangeCallback = Callable[["NodeDataChange"], None]


@dataclass(slots=True, frozen=True)
class NodeDataChange:
    """A single OPC UA DataChange notification."""

    node_id: str
    value: float | bool | int | str | None
    source_timestamp: datetime | None
    status_code: int | None = None
    quality: str = "good"

    @classmethod
    def from_raw(
        cls,
        node_id: str,
        value: float | bool | int | str | None,
        source_timestamp: datetime | None,
        status_code: int | None,
    ) -> NodeDataChange:
        return cls(
            node_id=node_id,
            value=value,
            source_timestamp=source_timestamp,
            status_code=status_code,
            quality=quality_from_status_code(status_code),
        )

    def to_node_read(self) -> NodeRead:
        """Convert to NodeRead used in snapshot construction path (reuses existing conversion logic)."""
        return NodeRead(
            node_id=self.node_id,
            value=self.value,
            source_timestamp=self.source_timestamp,
            status_code=self.status_code,
            quality=self.quality,
        )


@dataclass(slots=True)
class SubscriptionHandle:
    """Subscription handle and metadata."""

    subscription_id: int
    node_ids: list[str] = field(default_factory=list)
    sampling_interval_ms: float = 1000.0
    publishing_interval_ms: float = 1000.0
    status: str = SUBSCRIPTION_STATUS_ACTIVE


@runtime_checkable
class OpcUaSubscriptionClient(Protocol):
    """Minimal OPC UA subscription client protocol (read-only).

    ``read_node`` is used for initial cache seeding after subscription establishment.
    """

    endpoint: str

    @property
    def connected(self) -> bool: ...

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    async def read_node(self, node_id: str) -> NodeRead: ...

    async def subscribe(
        self,
        node_ids: Sequence[str],
        callback: DataChangeCallback,
        *,
        sampling_interval_ms: float = 1000.0,
        publishing_interval_ms: float = 1000.0,
    ) -> SubscriptionHandle: ...

    async def unsubscribe(self, handle: SubscriptionHandle) -> None: ...


def _coerce_value(raw: Any) -> float | bool | int | str | None:
    if raw is None or isinstance(raw, bool | int | float | str):
        return raw
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


class AsyncuaSubscriptionClient:
    """Real OPC UA subscription client based on ``asyncua`` (read-only).

    Receives DataChange notifications via ``create_subscription`` + ``subscribe_data_change``;
    holds no writable interfaces.
    """

    def __init__(self, endpoint: str, *, timeout_seconds: float = 4.0) -> None:
        self.endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._client: Any | None = None
        self._subscriptions: dict[int, Any] = {}

    @property
    def connected(self) -> bool:
        return self._client is not None

    async def connect(self) -> None:
        from asyncua import Client

        client = Client(self.endpoint, timeout=self._timeout_seconds)
        await client.connect()
        self._client = client

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None
            self._subscriptions.clear()

    async def read_node(self, node_id: str) -> NodeRead:
        if self._client is None:
            raise ConnectionError("OPC UA subscription client is not connected")
        node = self._client.get_node(node_id)
        data_value = await node.read_data_value()
        variant = getattr(data_value, "Value", None)
        raw_value = getattr(variant, "Value", None) if variant is not None else None
        status = getattr(data_value, "StatusCode", None)
        status_code = getattr(status, "value", None) if status is not None else None
        source_ts = getattr(data_value, "SourceTimestamp", None)
        return NodeRead(
            node_id=node_id,
            value=_coerce_value(raw_value),
            source_timestamp=_as_utc(source_ts),
            status_code=status_code,
            quality=quality_from_status_code(status_code),
        )

    async def subscribe(
        self,
        node_ids: Sequence[str],
        callback: DataChangeCallback,
        *,
        sampling_interval_ms: float = 1000.0,
        publishing_interval_ms: float = 1000.0,
    ) -> SubscriptionHandle:
        if self._client is None:
            raise ConnectionError("OPC UA subscription client is not connected")

        handler = _AsyncuaHandler(callback)
        subscription = await self._client.create_subscription(
            publishing_interval_ms, handler
        )
        nodes = [self._client.get_node(node_id) for node_id in node_ids]
        await subscription.subscribe_data_change(
            nodes, sampling_interval=sampling_interval_ms
        )
        handle = SubscriptionHandle(
            subscription_id=id(subscription) % 1_000_000,
            node_ids=list(node_ids),
            sampling_interval_ms=sampling_interval_ms,
            publishing_interval_ms=publishing_interval_ms,
        )
        self._subscriptions[handle.subscription_id] = subscription
        return handle

    async def unsubscribe(self, handle: SubscriptionHandle) -> None:
        subscription = self._subscriptions.pop(handle.subscription_id, None)
        if subscription is not None and self._client is not None:
            await subscription.delete()
        handle.status = SUBSCRIPTION_STATUS_STOPPED

    async def write_node(self, node_id: str, value: Any) -> None:
        """Explicitly reject write operations: subscriptions are read-only; see module docstring."""
        raise PermissionError(WRITE_REJECTED_MESSAGE)


class _AsyncuaHandler:
    """Normalize asyncua DataChange notification into :class:`NodeDataChange`."""

    def __init__(self, callback: DataChangeCallback) -> None:
        self._callback = callback

    def datachange_notification(self, node: Any, val: Any, data: Any) -> None:
        monitored_item = getattr(data, "monitored_item", None)
        data_value = getattr(monitored_item, "Value", None)
        if data_value is None and isinstance(val, (int, float, bool, str)):
            # Fallback: some servers only provide raw values.
            self._callback(
                NodeDataChange(
                    node_id=_node_id_string(node),
                    value=_coerce_value(val),
                    source_timestamp=None,
                    status_code=None,
                    quality=quality_from_status_code(None),
                )
            )
            return
        variant = getattr(data_value, "Value", None)
        raw_value = getattr(variant, "Value", None) if variant is not None else val
        status = getattr(data_value, "StatusCode", None)
        status_code = getattr(status, "value", None) if status is not None else None
        source_ts = getattr(data_value, "SourceTimestamp", None)
        self._callback(
            NodeDataChange.from_raw(
                node_id=_node_id_string(node),
                value=_coerce_value(raw_value),
                source_timestamp=_as_utc(source_ts),
                status_code=status_code,
            )
        )


def _node_id_string(node: Any) -> str:
    nodeid = getattr(node, "nodeid", None)
    to_string = getattr(nodeid, "to_string", None)
    if callable(to_string):
        result = to_string()
        return result if isinstance(result, str) else str(nodeid)
    return str(node)


class MockSubscriptionClient:
    """In-process subscription client (Mock mode / testing).

    Does not open network connections: test or Mock runtime injects DataChange events via :meth:`publish`,
    triggering callbacks synchronously within current event loop.
    """

    def __init__(
        self,
        endpoint: str = "mock://opcua-subscription",
        *,
        initial_provider: Callable[[str], NodeRead] | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.connected = False
        self._available = True
        self._initial_provider = initial_provider
        self._callbacks: list[DataChangeCallback] = []
        self._handles: dict[int, SubscriptionHandle] = {}
        self._next_id = 1
        self.published_count = 0
        self.delivered_count = 0

    @property
    def available(self) -> bool:
        return self._available

    def set_available(self, available: bool) -> None:
        self._available = available
        if not available:
            self.connected = False

    def set_initial_provider(self, provider: Callable[[str], NodeRead]) -> None:
        """Configure initial value provider (cache seeding after subscription established)."""
        self._initial_provider = provider

    async def connect(self) -> None:
        if not self._available:
            raise ConnectionError(f"Simulated OPC UA server unreachable: {self.endpoint}")
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def read_node(self, node_id: str) -> NodeRead:
        if not self.connected:
            raise ConnectionError("OPC UA subscription client is not connected")
        if self._initial_provider is None:
            raise ValueError("MockSubscriptionClient has no initial value provider configured")
        return self._initial_provider(node_id)

    async def subscribe(
        self,
        node_ids: Sequence[str],
        callback: DataChangeCallback,
        *,
        sampling_interval_ms: float = 1000.0,
        publishing_interval_ms: float = 1000.0,
    ) -> SubscriptionHandle:
        if not self.connected:
            raise ConnectionError("OPC UA subscription client is not connected")
        self._callbacks.append(callback)
        handle = SubscriptionHandle(
            subscription_id=self._next_id,
            node_ids=list(node_ids),
            sampling_interval_ms=sampling_interval_ms,
            publishing_interval_ms=publishing_interval_ms,
        )
        self._next_id += 1
        self._handles[handle.subscription_id] = handle
        return handle

    async def unsubscribe(self, handle: SubscriptionHandle) -> None:
        self._handles.pop(handle.subscription_id, None)
        if not self._handles:
            self._callbacks.clear()
        handle.status = SUBSCRIPTION_STATUS_STOPPED

    def publish(self, change: NodeDataChange) -> int:
        """Publish a DataChange event to all subscription callbacks, returning count of delivered callbacks."""
        self.published_count += 1
        delivered = 0
        for callback in self._callbacks:
            callback(change)
            delivered += 1
        self.delivered_count += delivered
        return delivered

    async def write_node(self, node_id: str, value: Any) -> None:
        """Explicitly reject write operations: subscriptions are read-only; see module docstring."""
        raise PermissionError(WRITE_REJECTED_MESSAGE)
