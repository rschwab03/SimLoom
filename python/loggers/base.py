import fnmatch
import warnings
from datetime import datetime, timezone

_GLOB_CHARS = set("*?[")


class Logger:
    """
    Base class for all loggers.

    Variables are registered from Python, so recording a new signal never
    requires rebuilding the C++ models:
      add(pattern)          a message bus key ("example/counter") or a glob ("example/*")
      add_value(name, val)  a Python-side constant (any JSON-serialisable value)

    The scheduler calls these hooks; subclasses override the ones they need:
      on_initialize(sched)      once, after every model_initialize()
      on_step(sched, model)     after every model_update()
      on_finalize(sched)        once, after every model_finalize()
    """

    def __init__(self) -> None:
        self._patterns: list[str] = []
        self._values: dict = {}

    def add(self, pattern: str) -> "Logger":
        self._patterns.append(pattern)
        return self

    def add_value(self, name: str, value) -> "Logger":
        self._values[name] = value
        return self

    def _resolve(self, bus) -> list[str]:
        """Expand registered patterns into concrete keys (order preserved, no duplicates).

        Missing exact keys are kept so they show up as null in the output.
        """
        available = bus.keys()
        resolved: list[str] = []
        for pattern in self._patterns:
            if _GLOB_CHARS & set(pattern):
                matches = fnmatch.filter(available, pattern)
                if not matches:
                    warnings.warn(f"{type(self).__name__}: pattern '{pattern}' matched no bus keys")
            else:
                matches = [pattern]
                if not bus.has(pattern):
                    warnings.warn(f"{type(self).__name__}: key '{pattern}' is not on the bus")
            resolved.extend(k for k in matches if k not in resolved)
        return resolved

    @staticmethod
    def _run_metadata(sched) -> dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration": sched.duration,
            "models": [
                {
                    "name": m.name,
                    "order": m.order,
                    "update_rate": m.update_rate,
                    "stop_time": m.stop_time,
                    "params": m.params,
                }
                for m in sorted(sched.models, key=lambda m: m.order)
            ],
        }

    def on_initialize(self, sched) -> None:
        pass

    def on_step(self, sched, model) -> None:
        pass

    def on_finalize(self, sched) -> None:
        pass
