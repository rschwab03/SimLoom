import ctypes
import glob
import heapq
import os

BUS_LIB = os.path.join(os.path.dirname(__file__), "..", "build", "message_bus.so")


class Model:
    """Wraps a compiled C++ shared library that implements model_interface.hpp."""

    def __init__(self, lib_path: str, order: int = None,
                 update_rate: float = None, stop_time: float = None):
        self._lib = ctypes.CDLL(lib_path)

        self._lib.model_name.restype = ctypes.c_char_p
        self._lib.model_update_rate.restype = ctypes.c_double
        self._lib.model_order.restype = ctypes.c_int
        self._lib.model_stop_time.restype = ctypes.c_double
        self._lib.model_initialize.restype = None
        self._lib.model_update.argtypes = [ctypes.c_double]
        self._lib.model_update.restype = None
        self._lib.model_finalize.restype = None

        self.name: str = self._lib.model_name().decode()
        self.order: int = order if order is not None else self._lib.model_order()
        self.update_rate: float = update_rate if update_rate is not None else self._lib.model_update_rate()
        self.stop_time: float = stop_time if stop_time is not None else self._lib.model_stop_time()
        self.dt: float = 1.0 / self.update_rate

    def initialize(self) -> None:
        self._lib.model_initialize()

    def update(self, sim_time: float) -> None:
        self._lib.model_update(sim_time)

    def finalize(self) -> None:
        self._lib.model_finalize()

    # Needed by heapq when two scheduled times are equal
    def __lt__(self, other: "Model") -> bool:
        return self.name < other.name


class Scheduler:
    """
    Simulation scheduler that executes C++ models at their specified update rates.

    Lifecycle:
      run() calls model_initialize() on all models in ascending model_order(),
      then drives the event loop, then calls model_finalize() on all models.

    Per-model stop_time:
      A model with stop_time >= 0 stops being updated once sim_time reaches
      that value. model_finalize() is still called for it at sim end.
    """

    def __init__(self) -> None:
        ctypes.CDLL(BUS_LIB, mode=ctypes.RTLD_GLOBAL)  # must precede model loads
        self._heap: list[tuple[float, Model]] = []
        self.sim_time: float = 0.0
        self.models: list[Model] = []

    def add_model(self, model: Model) -> None:
        """Register a Model instance with the scheduler."""
        self.models.append(model)

    def load_model(self, lib_path: str, order=None, update_rate=None, stop_time=None) -> Model:
        """Load a shared library, wrap it as a Model, and register it."""
        model = Model(lib_path, order=order, update_rate=update_rate, stop_time=stop_time)
        self.add_model(model)
        return model

    def load_models_from_dir(self, directory: str) -> None:
        """Load every .so file found in directory."""
        for path in sorted(glob.glob(os.path.join(directory, "*.so"))):
            self.load_model(path)

    def _initialize(self) -> None:
        for model in sorted(self.models, key=lambda m: m.order):
            model.initialize()
        for model in self.models:
            heapq.heappush(self._heap, (0.0, model))

    def _step(self) -> None:
        next_time, model = heapq.heappop(self._heap)
        self.sim_time = next_time
        model.update(self.sim_time)
        next_scheduled = next_time + model.dt
        # Re-queue only if the model's stop_time has not been reached
        if model.stop_time < 0.0 or next_scheduled <= model.stop_time:
            heapq.heappush(self._heap, (next_scheduled, model))

    def _finalize(self) -> None:
        for model in self.models:
            model.finalize()

    def run(self, duration: float) -> None:
        """Run the full simulation lifecycle for the given duration (seconds)."""
        self._initialize()
        while self._heap and self._heap[0][0] < duration:
            self._step()
        self._finalize()
