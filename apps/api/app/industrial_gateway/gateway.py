"""Industrial protocol gateway facade: configuration parsing and client factories.

Configuration comes entirely from environment variables (see ``GATEWAY_*`` in ``app.core.config.Settings``),
disabled by default (``GATEWAY_ENABLED=false``), preserving existing mock pipelines.

Subscription (event-driven) and polling clients coexist:
Polling is used for ``sync_once`` periodic reads, subscription is used for DataChange event-driven ingestion,
both sharing the downstream quality layer and AI pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.core.config import Settings
from app.industrial_gateway.opcua.client import (
    AsyncuaOpcUaClient,
    MockOpcUaClient,
    OpcUaClient,
)
from app.industrial_gateway.opcua.subscription import (
    AsyncuaSubscriptionClient,
    MockSubscriptionClient,
    OpcUaSubscriptionClient,
)

GATEWAY_MODE_MOCK: Final = "mock"
GATEWAY_MODE_OPCUA: Final = "opcua"
SUPPORTED_GATEWAY_MODES: Final[frozenset[str]] = frozenset(
    {GATEWAY_MODE_MOCK, GATEWAY_MODE_OPCUA}
)

DEFAULT_ENDPOINT = "opc.tcp://127.0.0.1:4840/industrial-simulator/"
DEFAULT_MOCK_ENDPOINT = "mock://opcua-simulator"
DEFAULT_SUBSCRIPTION_MOCK_ENDPOINT = "mock://opcua-subscription"


@dataclass(slots=True, frozen=True)
class GatewayConfig:
    """Gateway runtime configuration (derived from Settings, read-only)."""

    enabled: bool
    mode: str
    endpoint: str
    poll_interval_seconds: float
    auto_ingest: bool
    mapping_config_path: str
    timeout_seconds: float
    subscription_enabled: bool = False
    subscription_sampling_ms: float = 1000.0
    subscription_debounce_ms: float = 1000.0
    read_only: bool = True

    @classmethod
    def from_settings(cls, settings: Settings) -> GatewayConfig:
        mode = settings.GATEWAY_MODE.strip().lower()
        if mode not in SUPPORTED_GATEWAY_MODES:
            raise ValueError(
                f"GATEWAY_MODE only supports {sorted(SUPPORTED_GATEWAY_MODES)}, currently {mode!r}"
            )
        endpoint = settings.GATEWAY_ENDPOINT.strip()
        if not endpoint:
            endpoint = (
                DEFAULT_ENDPOINT
                if mode == GATEWAY_MODE_OPCUA
                else DEFAULT_MOCK_ENDPOINT
            )
        return cls(
            enabled=settings.GATEWAY_ENABLED,
            mode=mode,
            endpoint=endpoint,
            poll_interval_seconds=max(settings.GATEWAY_POLL_INTERVAL_SECONDS, 1.0),
            auto_ingest=settings.GATEWAY_AUTO_INGEST,
            mapping_config_path=settings.GATEWAY_MAPPING_CONFIG,
            timeout_seconds=settings.GATEWAY_TIMEOUT_SECONDS,
            subscription_enabled=settings.GATEWAY_SUBSCRIPTION_ENABLED,
            subscription_sampling_ms=settings.GATEWAY_SUBSCRIPTION_SAMPLING_MS,
            subscription_debounce_ms=settings.GATEWAY_SUBSCRIPTION_DEBOUNCE_MS,
        )


def build_client(config: GatewayConfig) -> OpcUaClient:
    """Build read-only OPC UA polling client by mode."""
    if config.mode == GATEWAY_MODE_OPCUA:
        return AsyncuaOpcUaClient(
            config.endpoint, timeout_seconds=config.timeout_seconds
        )
    return MockOpcUaClient(endpoint=config.endpoint)


def build_subscription_client(config: GatewayConfig) -> OpcUaSubscriptionClient:
    """Build read-only OPC UA subscription client (event-driven) by mode."""
    if config.mode == GATEWAY_MODE_OPCUA:
        return AsyncuaSubscriptionClient(
            config.endpoint, timeout_seconds=config.timeout_seconds
        )
    return MockSubscriptionClient(endpoint=DEFAULT_SUBSCRIPTION_MOCK_ENDPOINT)
