"""Alarm Intelligence (AI-assisted industrial alarm analysis).

Positioning: **AI-assisted industrial alarm analysis** -- performs correlation grouping,
semantic understanding, root cause analysis, and maintenance decision support on persisted IndustrialAlarms.

Boundaries (key constraints):

- Read-only consumer layer: does not alter OPC UA Gateway / Subscription / alarm production paths;
- Does not modify ML models or experiment results; analysis relies on deterministic rules + existing knowledge retrieval;
- **Advisory only**: does not create or execute device controls; all operations must proceed via
  existing WorkOrder + Human Approval (OperationApproval) workflows.

Structure::

├── __init__.py      # Facade and public exports
├── correlation.py   # Correlation engine: merges related alarms into event groups (deterministic rules)
└── engine.py        # Understanding, RCA, and decision support (rules + knowledge retrieval)
"""

from __future__ import annotations

MODULE_NAME = "alarm_intelligence"

__all__ = ["MODULE_NAME"]
