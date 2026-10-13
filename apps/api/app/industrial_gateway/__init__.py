"""Industrial Protocol Gateway layer.

Currently implements OPC UA read-only telemetry ingestion:
OPC UA Device Layer -> Gateway -> Validation -> Telemetry -> AI Platform

Responsibility boundaries:

- Read device data only; all PLC write operations prohibited by default;
- Raw node reads must pass Data Quality Layer validation before entering business workflows;
- Node-to-equipment asset mappings are fully configurable (database table + YAML config);
- Reuses ``intelligence_service.ingest_snapshot`` without bypassing any AI capabilities.

Module structure::

├── opcua/          # OPC UA Client abstractions and implementations
├── simulator/      # Software OPC UA device simulator (Demo without physical PLCs)
├── models.py       # GatewayConnection / OpcUaNodeMapping database models
├── mapping.py      # Node -> equipment asset mapping
└── gateway.py      # Configuration and client factories
"""

from __future__ import annotations

MODULE_NAME = "industrial_gateway"

__all__ = ["MODULE_NAME"]
