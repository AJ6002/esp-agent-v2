"""Repeatable compatible migrations.

Preserves incremental upgrade runner as migration entrypoint; downgrades remove new platform tables only,
preserving historical work orders without dropping compatibility columns.
"""

from __future__ import annotations

import uuid
from contextlib import nullcontext

from sqlalchemy import Connection, Engine, inspect, text
from sqlalchemy.schema import DropTable

_CHECKLIST_CATEGORIES = {
    "safety": [
        "Equipment powered off",
        "Associated power sources disconnected",
        "Lockout/Tagout (LOTO) executed",
        "Residual energy dissipated",
        "Safety interlocks verified",
        "Site warning signs placed",
        "PPE worn",
        "Confirm equipment powered off",
        "Execute power cutoff",
        "Execute Lockout/Tagout (LOTO)",
        "Confirm residual energy dissipated",
    ],
    "diagnosis": ["Read and record fault code", "Check relevant component status"],
    "testing": ["No-load test", "Load test", "Confirm equipment restored to normal"],
}

INTELLIGENT_MAINTENANCE_TABLES = (
    "equipment_sensors",
    "telemetry_records",
    "anomaly_events",
    "fault_diagnoses",
    "risk_predictions",
    "maintenance_recommendations",
    "spare_part_reservations",
    "operation_approvals",
    "operation_execution_audits",
    "maintenance_verifications",
    "agent_runs",
    "tool_invocations",
    "ml_dataset_versions",
    "ml_feature_definitions",
    "ml_training_runs",
    "ml_model_versions",
    "ml_model_metrics",
    "ml_prediction_records",
)

_INTELLIGENCE_DROP_ORDER = tuple(reversed(INTELLIGENT_MAINTENANCE_TABLES))


def upgrade_schema(engine: Engine | Connection) -> list[str]:
    """Upgrade to current head, returning migration names actually applied."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    applied: list[str] = []

    transaction = (
        nullcontext(engine) if isinstance(engine, Connection) else engine.begin()
    )
    with transaction as connection:
        if "work_order_checklist_items" in table_names:
            columns = {
                column["name"]
                for column in inspector.get_columns("work_order_checklist_items")
            }
            if "category" not in columns:
                connection.execute(
                    text(
                        "ALTER TABLE work_order_checklist_items "
                        "ADD COLUMN category VARCHAR(32) NOT NULL DEFAULT 'repair'"
                    )
                )
                applied.append("work_order_checklist_items.category")

            backfilled = False
            for category, contents in _CHECKLIST_CATEGORIES.items():
                for content in contents:
                    result = connection.execute(
                        text(
                            "UPDATE work_order_checklist_items "
                            "SET category = :category "
                            "WHERE content = :content AND category = 'repair'"
                        ),
                        {"category": category, "content": content},
                    )
                    backfilled = bool(result.rowcount) or backfilled
            if backfilled:
                applied.append("work_order_checklist_items.category_backfill")

        if "equipment" in table_names:
            equipment_columns = {
                column["name"] for column in inspector.get_columns("equipment")
            }
            additions = {
                "asset_uuid": "VARCHAR(32)",
                "next_maintenance_at": "DATE",
                "health_score": "FLOAT NOT NULL DEFAULT 100",
                "rated_parameters": "JSON",
                "cumulative_runtime_hours": "FLOAT NOT NULL DEFAULT 0",
            }
            for column_name, sql_type in additions.items():
                if column_name not in equipment_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE equipment ADD COLUMN {column_name} {sql_type}"
                        )
                    )
                    applied.append(f"equipment.{column_name}")

            rows = connection.execute(
                text("SELECT id FROM equipment WHERE asset_uuid IS NULL")
            ).all()
            for row in rows:
                stable_uuid = uuid.uuid5(
                    uuid.NAMESPACE_URL, f"industrial-maintenance-equipment:{row.id}"
                ).hex
                connection.execute(
                    text(
                        "UPDATE equipment SET asset_uuid = :asset_uuid WHERE id = :id"
                    ),
                    {"asset_uuid": stable_uuid, "id": row.id},
                )
            if rows:
                applied.append("equipment.asset_uuid_backfill")

            if connection.dialect.name == "postgresql":
                for enum_value in ("idle", "warning", "maintenance", "offline"):
                    connection.execute(
                        text(
                            "ALTER TYPE equipmentstatusenum "
                            f"ADD VALUE IF NOT EXISTS '{enum_value}'"
                        )
                    )

        if "ml_dataset_versions" in table_names:
            dataset_columns = {
                column["name"]
                for column in inspector.get_columns("ml_dataset_versions")
            }
            if "processed_sha256" not in dataset_columns:
                connection.execute(
                    text(
                        "ALTER TABLE ml_dataset_versions "
                        "ADD COLUMN processed_sha256 VARCHAR(64)"
                    )
                )
                applied.append("ml_dataset_versions.processed_sha256")

        if "operation_approvals" in table_names:
            approval_columns = {
                column["name"]
                for column in inspector.get_columns("operation_approvals")
            }
            if "execution_key" not in approval_columns:
                connection.execute(
                    text(
                        "ALTER TABLE operation_approvals "
                        "ADD COLUMN execution_key VARCHAR(64)"
                    )
                )
                approval_ids = connection.execute(
                    text("SELECT id FROM operation_approvals")
                ).scalars()
                for approval_id in approval_ids:
                    execution_key = uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"industrial-maintenance-operation-approval:{approval_id}",
                    ).hex
                    connection.execute(
                        text(
                            "UPDATE operation_approvals "
                            "SET execution_key = :execution_key WHERE id = :id"
                        ),
                        {"execution_key": execution_key, "id": approval_id},
                    )
                applied.append("operation_approvals.execution_key")
            datetime_sql = (
                "TIMESTAMP WITH TIME ZONE"
                if connection.dialect.name == "postgresql"
                else "DATETIME"
            )
            reconciliation_additions = {
                "execution_started_at": datetime_sql,
                "execution_attempt": "INTEGER NOT NULL DEFAULT 0",
                "reconciliation_outcome": "VARCHAR(32)",
                "reconciliation_note": "TEXT",
                "observed_device_state": "TEXT",
                "reconciled_by": "INTEGER",
                "reconciled_at": datetime_sql,
            }
            reconciliation_added = False
            for column_name, sql_type in reconciliation_additions.items():
                if column_name not in approval_columns:
                    connection.execute(
                        text(
                            "ALTER TABLE operation_approvals "
                            f"ADD COLUMN {column_name} {sql_type}"
                        )
                    )
                    reconciliation_added = True
            if reconciliation_added and {"status", "reviewed_at"}.issubset(
                approval_columns
            ):
                connection.execute(
                    text(
                        "UPDATE operation_approvals "
                        "SET execution_started_at = reviewed_at "
                        "WHERE status = 'executing' "
                        "AND execution_started_at IS NULL"
                    )
                )
            if reconciliation_added:
                applied.append("operation_approvals.execution_reconciliation")
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS "
                    "ix_operation_approvals_execution_key "
                    "ON operation_approvals (execution_key)"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS "
                    "ix_operation_approvals_execution_started_at "
                    "ON operation_approvals (execution_started_at)"
                )
            )

    # Import models centrally to ensure metadata contains all tables.
    import app.models  # noqa: F401
    from app.db.session import Base

    before_create = set(inspect(engine).get_table_names())
    Base.metadata.create_all(bind=engine)
    for table_name, index_name in (
        ("ml_model_versions", "uq_ml_model_active_production_task"),
        ("ml_feature_definitions", "uq_ml_feature_schema_name"),
    ):
        required_index = next(
            index
            for index in Base.metadata.tables[table_name].indexes
            if index.name == index_name
        )
        required_index.create(bind=engine, checkfirst=True)
    after_create = set(inspect(engine).get_table_names())
    if set(INTELLIGENT_MAINTENANCE_TABLES) - before_create and set(
        INTELLIGENT_MAINTENANCE_TABLES
    ).issubset(after_create):
        applied.append("intelligent_maintenance.head")

    return applied


def downgrade_intelligent_schema(engine: Engine) -> list[str]:
    """Roll back to legacy work order compatible version, preserving legacy tables and equipment columns.

    Used for migration drills and emergency rollback. Drops data in intelligent maintenance tables;
    backup first in production environments.
    """
    import app.models  # noqa: F401
    from app.db.session import Base

    existing = set(inspect(engine).get_table_names())
    dropped: list[str] = []
    with engine.begin() as connection:
        for table_name in _INTELLIGENCE_DROP_ORDER:
            if table_name not in existing:
                continue
            connection.execute(
                DropTable(Base.metadata.tables[table_name], if_exists=True)
            )
            dropped.append(table_name)
    return dropped


def schema_is_ready(engine: Engine) -> bool:
    """Check whether current database contains core tables required for platform operation."""
    tables = set(inspect(engine).get_table_names())
    return {"users", "equipment", "work_orders"}.issubset(tables) and set(
        INTELLIGENT_MAINTENANCE_TABLES
    ).issubset(tables)
