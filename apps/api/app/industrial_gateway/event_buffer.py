"""Event Buffer: final aggregation before DataChange events enter snapshot construction.

Responsibilities:

- **batch aggregation**: Retain latest value per node within debounce window
  (e.g. Temperature changes 10 times in 1 second -> aggregated into 1 outgoing event);
- **debounce**: Release after ``debounce_seconds`` elapsed since earliest event in window;
- **duplicate suppression**: Suppress events on same node when timestamp does not advance,
  consistent with snapshot path quality dedup rules.

Zero external dependencies like Redis/Kafka: purely in-process memory buffer + injectable clock.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.industrial_gateway.opcua.subscription import NodeDataChange

OUTCOME_ACCEPTED = "accepted"
OUTCOME_DUPLICATE = "duplicate"


class EventBuffer:
    """Bounded per-node aggregated DataChange event buffer."""

    def __init__(
        self,
        *,
        debounce_seconds: float = 1.0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if debounce_seconds <= 0:
            raise ValueError("debounce_seconds must be positive")
        self._debounce_seconds = debounce_seconds
        self._clock = clock or (lambda: datetime.now(UTC))
        self._pending: dict[str, NodeDataChange] = {}
        self._last_timestamps: dict[str, datetime] = {}
        self.accepted_count = 0
        self.duplicate_count = 0

    @property
    def debounce_seconds(self) -> float:
        return self._debounce_seconds

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def add(self, event: NodeDataChange) -> str:
        """Add to buffer; returns ``accepted`` or ``duplicate``.

        Substitutes current clock when timestamp is missing; suppresses duplicates when node timestamp does not advance.
        """
        timestamp = event.source_timestamp or self._clock()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        last = self._last_timestamps.get(event.node_id)
        if last is not None and timestamp <= last:
            self.duplicate_count += 1
            return OUTCOME_DUPLICATE
        normalized = (
            NodeDataChange(
                node_id=event.node_id,
                value=event.value,
                source_timestamp=timestamp,
                status_code=event.status_code,
                quality=event.quality,
            )
            if event.source_timestamp is not timestamp
            else event
        )
        # batch aggregation: keep latest event per node within window.
        self._pending[event.node_id] = normalized
        self._last_timestamps[event.node_id] = timestamp
        self.accepted_count += 1
        return OUTCOME_ACCEPTED

    def drain_due(self, now: datetime | None = None) -> list[NodeDataChange]:
        """Return all events for due batch (latest value per node) and clear pending."""
        if not self._pending:
            return []
        current = now or self._clock()
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        timestamps = [
            event.source_timestamp
            for event in self._pending.values()
            if event.source_timestamp is not None
        ]
        if not timestamps:
            return []
        if (current - min(timestamps)).total_seconds() < self._debounce_seconds:
            return []
        drained = list(self._pending.values())
        self._pending.clear()
        return drained

    def force_drain(self) -> list[NodeDataChange]:
        """Flush all pending immediately ignoring debounce (stopping subscription / testing)."""
        drained = list(self._pending.values())
        self._pending.clear()
        return drained

    def reset(self) -> None:
        self._pending.clear()
        self._last_timestamps.clear()
