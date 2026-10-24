import json
import os

from .base import Logger


class InitialConditionLogger(Logger):
    """
    Records a one-time snapshot of signals right after initialization.

    Use this for initial conditions and constant inputs that never change during
    a run. The JSON file is written immediately, so it survives a later crash.

    Output layout:
      {"run": {...metadata...}, "signals": {key: value}, "values": {name: value}}
    """

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    def on_initialize(self, sched) -> None:
        bus = sched.bus
        record = {
            "run": self._run_metadata(sched),
            "signals": {k: (bus.get(k) if bus.has(k) else None) for k in self._resolve(bus)},
            "values": self._values,
        }
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(record, f, indent=2)
