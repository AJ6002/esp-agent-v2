"""Deterministic industrial motor simulation generator (pure function, zero network dependencies).

Design constraints:

- **Reproducible**: Values determined solely by ``(seed, scenario, tick)``;
  identical runs guaranteed with fixed random seed;
- **Ranges match specifications**: Temperature 20-100 deg C, Vibration 0-5 mm/s,
  Current 10-35 A, Voltage 340-420 V, LoadRatio 0-120%;
- **Three states**: normal / warning / fault (warning and fault degrade gradually
  after warmup ticks, fault activates Alarm bit).

Used in two locations:

1. ``simulator.opcua_server``: Publishes values to real OPC UA Server;
2. ``opcua.client.MockOpcUaClient``: In-process Mock mode (when asyncua is not installed).
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Final

SCENARIO_NORMAL: Final = "normal"
SCENARIO_WARNING: Final = "warning"
SCENARIO_FAULT: Final = "fault"
SUPPORTED_SCENARIOS: Final[frozenset[str]] = frozenset(
    {SCENARIO_NORMAL, SCENARIO_WARNING, SCENARIO_FAULT}
)

# Node name and NodeId suffix (ns determined when registered by OPC UA Server, demo is ns=2).
NODE_NAMES: Final[tuple[str, ...]] = (
    "Temperature",
    "Vibration",
    "Current",
    "Speed",
    "Voltage",
    "LoadRatio",
    "RunningState",
    "Alarm",
)

# Specification ranges (including demo voltage / load ratio extension nodes).
METRIC_RANGES: Final[dict[str, tuple[float, float]]] = {
    "Temperature": (20.0, 100.0),
    "Vibration": (0.0, 5.0),
    "Current": (0.0, 20.0),
    "Speed": (0.0, 3000.0),
    "Voltage": (340.0, 420.0),
    "LoadRatio": (0.0, 120.0),
}

# normal condition baseline (all within platform health thresholds).
_BASELINE: Final[dict[str, float]] = {
    "Temperature": 55.0,
    "Vibration": 1.8,
    "Current": 12.0,
    "Speed": 1480.0,
    "Voltage": 380.0,
    "LoadRatio": 60.0,
}

# Warmup ticks before degradation begins for each scenario.
_WARMUP_TICKS: Final[dict[str, int]] = {
    SCENARIO_NORMAL: 0,
    SCENARIO_WARNING: 5,
    SCENARIO_FAULT: 3,
}


def _clamp(name: str, value: float) -> float:
    low, high = METRIC_RANGES[name]
    return min(max(value, low), high)


@dataclass(slots=True)
class MotorSimulator:
    """Industrial Motor deterministic simulator.

    ``advance()`` records differences from previous tick (``changed_nodes``),
    serving as DataChange subscription event source: same ``(seed, scenario, tick)``
    always yields identical values and event sequences.
    """

    seed: int = 42
    scenario: str = SCENARIO_NORMAL
    prefix: str = "Motor001"
    _tick: int = field(default=0, init=False)
    _current: dict[str, float | bool] = field(default_factory=dict, init=False)
    _current_at: datetime | None = field(default=None, init=False)
    _previous: dict[str, float | bool] = field(default_factory=dict, init=False)
    _changes: dict[str, bool] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.scenario not in SUPPORTED_SCENARIOS:
            raise ValueError(
                f"Unsupported simulation scenario: {self.scenario} (supported: {sorted(SUPPORTED_SCENARIOS)})"
            )
        self.advance()

    @property
    def tick(self) -> int:
        return self._tick

    @property
    def changed_nodes(self) -> tuple[str, ...]:
        """Node names changed in latest advance (DataChange event source)."""
        return tuple(name for name, changed in self._changes.items() if changed)

    def node_ids(self, namespace: int = 2) -> list[str]:
        """All string NodeIds exposed by device (default ns=2)."""
        return [f"ns={namespace};s={self.prefix}.{name}" for name in NODE_NAMES]

    def set_scenario(self, scenario: str) -> None:
        """Switch scenario and deterministically reset to tick 0 for that scenario (Demo control).

        Modifies internal simulator state only; produces zero external writes.
        """
        if scenario not in SUPPORTED_SCENARIOS:
            raise ValueError(
                f"Unsupported simulation scenario: {scenario} (supported: {sorted(SUPPORTED_SCENARIOS)})"
            )
        self.scenario = scenario
        self._tick = 0
        self._current = {}
        self._previous = {}
        self._changes = {}
        self.advance()

    def advance(self) -> dict[str, float | bool]:
        """Advance one sampling period and return current value snapshot (deterministic)."""
        rng = random.Random(f"{self.seed}:{self.scenario}:{self._tick}")
        values: dict[str, float | bool] = {
            "Temperature": _BASELINE["Temperature"] + rng.uniform(-0.8, 0.8),
            "Vibration": _BASELINE["Vibration"] + rng.uniform(-0.15, 0.15),
            "Current": _BASELINE["Current"] + rng.uniform(-0.4, 0.4),
            "Speed": _BASELINE["Speed"] + rng.uniform(-8.0, 8.0),
            "Voltage": _BASELINE["Voltage"] + rng.uniform(-2.0, 2.0),
            "LoadRatio": _BASELINE["LoadRatio"] + rng.uniform(-2.0, 2.0),
            "RunningState": True,
            "Alarm": False,
        }

        warmup = _WARMUP_TICKS[self.scenario]
        elapsed = max(self._tick - warmup, 0)
        if self.scenario == SCENARIO_WARNING and elapsed > 0:
            # Bearing temperature slowly climbs past warning threshold (>75 C), vibration moderately rises.
            values["Temperature"] += min(elapsed * 1.6, 32.0)
            values["Vibration"] += min(elapsed * 0.12, 1.6)
            values["LoadRatio"] += min(elapsed * 0.4, 6.0)
        elif self.scenario == SCENARIO_FAULT and elapsed > 0:
            # Fault initial tick: vibration surges suddenly (immediately visible in DataChange).
            if elapsed == 1:
                values["Vibration"] += 2.2
            # Severe degradation: temperature rise + vibration + overcurrent, alarm bit activated.
            values["Temperature"] += min(elapsed * 3.2, 44.0)
            values["Vibration"] += min(elapsed * 0.55, 3.1)
            values["Current"] += min(elapsed * 0.9, 7.5)
            values["Speed"] -= min(elapsed * 12.0, 120.0)
            values["Alarm"] = True

        for name in METRIC_RANGES:
            values[name] = round(_clamp(name, float(values[name])), 2)

        # Change detection: compared against previous tick for subscription event source.
        self._changes = {
            name: name not in self._previous or self._previous[name] != value
            for name, value in values.items()
        }
        self._previous = dict(values)
        self._tick += 1
        self._current = values
        self._current_at = datetime.now(UTC)
        return dict(values)

    def current_values(self) -> dict[str, float | bool]:
        """Value snapshot of latest advance()."""
        return dict(self._current)

    def value_provider(
        self,
    ) -> Callable[[str], tuple[float | bool | None, datetime | None]]:
        """Return node getter function compatible with ``MockOpcUaClient``.

        Values always originate from same tick snapshot, ensuring cross-node consistency in single sync.
        """

        def provider(node_id: str) -> tuple[float | bool | None, datetime | None]:
            prefix, _, name = node_id.rpartition(".")
            if prefix != f"ns=2;s={self.prefix}" or name not in NODE_NAMES:
                return None, self._current_at
            return self._current.get(name), self._current_at

        return provider
