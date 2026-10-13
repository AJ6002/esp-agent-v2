"""Software OPC UA Server: simulates industrial equipment (Industrial Motor).

Purpose: Provides an OPC UA Server behaving identically to physical equipment
for end-to-end demos when physical PLCs are unavailable.

Node layout (namespace default is ns=2 after registration)::

    ns=2;s=Motor001.RunningState     Boolean     read-only
    ns=2;s=Motor001.Temperature      Double      read-only
    ns=2;s=Motor001.Vibration        Double      read-only
    ns=2;s=Motor001.Current          Double      read-only
    ns=2;s=Motor001.Alarm            Boolean     read-only
    ns=2;s=Motor001.Voltage          Double      read-only
    ns=2;s=Motor001.LoadRatio        Double      read-only

├── Voltage       340-420 V   (extension node, for AI pipeline assessment)
├── LoadRatio     0-120 %     (extension node, for AI pipeline assessment)

Values generated via deterministic seeded generator in :mod:`.generator`,
supporting reproducible runs via ``--seed`` and normal / warning / fault scenarios.

Run::

    python -m app.industrial_gateway.simulator.opcua_server --scenario warning

Security note: simulator serves solely as a data source; gateway is strictly read-only,
and this process implements zero client write permissions.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Any

from app.industrial_gateway.simulator.generator import (
    NODE_NAMES,
    SUPPORTED_SCENARIOS,
    MotorSimulator,
)

logger = logging.getLogger("app.industrial_gateway.simulator")

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 4840
DEFAULT_PATH = "/industrial-simulator/"
NAMESPACE_URI = "http://industrial-maintenance.local/opcua-simulator/"
DEFAULT_NAMESPACE_INDEX = 2


class OpcUaSimulatorServer:
    """Publish deterministic values from MotorSimulator as real OPC UA variables."""

    def __init__(
        self,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        path: str = DEFAULT_PATH,
        seed: int = 42,
        scenario: str = "normal",
        prefix: str = "Motor001",
        namespace_index: int = DEFAULT_NAMESPACE_INDEX,
    ) -> None:
        if scenario not in SUPPORTED_SCENARIOS:
            raise ValueError(f"Unsupported simulation scenario: {scenario}")
        self._endpoint = f"opc.tcp://{host}:{port}{path}"
        self._seed = seed
        self._scenario = scenario
        self._prefix = prefix
        self._namespace_index = namespace_index
        self._simulator = MotorSimulator(seed=seed, scenario=scenario, prefix=prefix)
        self._server: Any | None = None
        self._variables: dict[str, Any] = {}

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def simulator(self) -> MotorSimulator:
        return self._simulator

    async def start(self) -> None:
        from asyncua import Server, ua

        server = Server()
        await server.init()
        server.set_endpoint(self._endpoint)
        server.set_server_name("Industrial Maintenance OPC UA Device Simulator")
        # Reserve namespace index to guarantee stable demo NodeId ns=2;s=Motor001.*.
        registered = await server.register_namespace(NAMESPACE_URI)
        if registered != self._namespace_index:
            logger.warning(
                "namespace index actual is ns=%d (demo mappings default to ns=%d)",
                registered,
                self._namespace_index,
            )
            self._namespace_index = registered

        objects = server.nodes.objects
        device = await objects.add_object(
            ua.NodeId(self._prefix, self._namespace_index),
            ua.QualifiedName(self._prefix, self._namespace_index),
        )
        initial = self._simulator.current_values()
        for name in NODE_NAMES:
            variable = await device.add_variable(
                ua.NodeId(f"{self._prefix}.{name}", self._namespace_index),
                ua.QualifiedName(name, self._namespace_index),
                initial[name],
            )
            # set_writable omitted: variables remain read-only for clients.
            self._variables[name] = variable

        await server.start()
        self._server = server
        logger.info(
            "OPC UA simulator started: %s (seed=%d, scenario=%s)",
            self._endpoint,
            self._seed,
            self._scenario,
        )

    async def stop(self) -> None:
        if self._server is not None:
            await self._server.stop()
            self._server = None
            logger.info("OPC UA simulator stopped")

    async def publish_tick(self) -> dict[str, float | bool]:
        """Advance simulation and write all variables."""
        values = self._simulator.advance()
        for name, value in values.items():
            await self._variables[name].write_value(value)
        return values

    async def serve_forever(self, interval_seconds: float = 1.0) -> None:
        """Start server and publish data at fixed intervals."""
        await self.start()
        try:
            while True:
                await asyncio.sleep(interval_seconds)
                values = await self.publish_tick()
                logger.debug("tick published: %s", values)
        finally:
            await self.stop()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Industrial Motor OPC UA simulation server (deterministic, reproducible)"
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--path", default=DEFAULT_PATH)
    parser.add_argument("--seed", type=int, default=42, help="Fixed random seed")
    parser.add_argument(
        "--scenario",
        default="normal",
        choices=sorted(SUPPORTED_SCENARIOS),
        help="Execution scenario: normal / warning / fault",
    )
    parser.add_argument("--interval", type=float, default=1.0, help="Publish interval (seconds)")
    parser.add_argument("--prefix", default="Motor001", help="Equipment node prefix")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        server = OpcUaSimulatorServer(
            host=args.host,
            port=args.port,
            path=args.path,
            seed=args.seed,
            scenario=args.scenario,
            prefix=args.prefix,
        )
        asyncio.run(server.serve_forever(interval_seconds=args.interval))
    except KeyboardInterrupt:
        logger.info("Interrupt received, simulator exiting")
    except ImportError as exc:  # pragma: no cover - actionable hint when environment lacks dependency
        logger.error("Running OPC UA simulator requires asyncua: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
