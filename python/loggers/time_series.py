import json
import os

from .base import Logger
from .convert import json_to_csv


class TimeSeriesLogger(Logger):
    """
    Records signals over time: once at t = 0 (the initial state, right after
    every model_initialize()), then at the end of each frame.

    Use this for time-dependent signals. With rate=None a sample is taken every
    frame (every sim_time at which any model updated); with rate=<Hz> samples
    are taken at the first frame at or after each multiple of 1/rate.

    Patterns are resolved at the t = 0 sample, so globs match keys published
    during model_initialize(). An exact key first published later records null
    until it appears.

    Output layout (column-oriented, one entry per sample):
      {"run": {...metadata...}, "values": {name: value},
       "t": [t0, t1, ...], "signals": {key: [v0, v1, ...]}}

    Data is held in memory and written at finalize. Pass csv=True to also write
    a CSV next to the JSON (same path, .csv extension).
    """

    _EPS = 1e-9

    def __init__(self, path: str, rate: float = None, csv: bool = False) -> None:
        super().__init__()
        self.path = path
        self.rate = rate
        self.csv = csv
        self._keys: list[str] = None
        self._t: list[float] = []
        self._columns: dict[str, list] = {}
        self._sample_index = 0

    def on_initialize(self, sched) -> None:
        self.on_frame(sched)  # sim_time is 0: record the initial state

    def on_frame(self, sched) -> None:
        if self.rate is not None:
            if sched.sim_time < self._sample_index / self.rate - self._EPS:
                return
            # Skip ahead past every sample time this frame covers
            while self._sample_index / self.rate <= sched.sim_time + self._EPS:
                self._sample_index += 1

        bus = sched.bus
        if self._keys is None:
            self._keys = self._resolve(bus)
            self._columns = {k: [] for k in self._keys}

        self._t.append(sched.sim_time)
        for k in self._keys:
            self._columns[k].append(bus.get(k) if bus.has(k) else None)

    def on_finalize(self, sched) -> None:
        record = {
            "run": self._run_metadata(sched),
            "values": self._values,
            "t": self._t,
            "signals": self._columns,
        }
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(record, f, indent=2)
        if self.csv:
            json_to_csv(self.path)
