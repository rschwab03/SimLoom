import ctypes
import glob
import heapq
import os
import shutil
import tempfile
import warnings

from bus import MessageBus

BUS_LIB = os.path.join(os.path.dirname(__file__), "..", "build", "message_bus.so")

# Per-instance copies of model libraries. The copies must outlive the process's
# use of them: glibc identifies loaded libraries by inode, so deleting a copy
# early could let a new copy reuse the inode and alias the old library.
_INSTANCE_DIR = tempfile.TemporaryDirectory(prefix="simloom_instances_")


class Model:
    """
    Wraps a compiled C++ shared library that implements model_interface.hpp.

    Pass instance="<name>" to load an independent copy of the library, with its
    own static state, so one model can be instantiated several times. The name
    is passed to the model's optional model_set_instance() before anything else
    and becomes this Model's name.

    An update_rate of 0 means the model is not clock-driven: it is initialized
    and finalized but never scheduled for model_update().
    """

    def __init__(self, lib_path: str, order: int = None,
                 update_rate: float = None, stop_time: float = None,
                 params: dict = None, instance: str = None):
        if instance is not None:
            stem = os.path.splitext(os.path.basename(lib_path))[0]
            copy_path = os.path.join(_INSTANCE_DIR.name, f"{stem}__{instance}.so")
            shutil.copy2(lib_path, copy_path)
            self._lib = ctypes.CDLL(copy_path)
        else:
            self._lib = ctypes.CDLL(lib_path)

        if instance is not None:
            if hasattr(self._lib, "model_set_instance"):
                self._lib.model_set_instance.argtypes = [ctypes.c_char_p]
                self._lib.model_set_instance.restype = None
                self._lib.model_set_instance(instance.encode())
            else:
                warnings.warn(f"{lib_path} has no model_set_instance(); instance "
                              f"'{instance}' gets its own state but may share bus keys")

        self._lib.model_name.restype = ctypes.c_char_p
        self._lib.model_update_rate.restype = ctypes.c_double
        self._lib.model_order.restype = ctypes.c_int
        self._lib.model_stop_time.restype = ctypes.c_double
        self._lib.model_initialize.restype = None
        self._lib.model_update.argtypes = [ctypes.c_double]
        self._lib.model_update.restype = None
        self._lib.model_finalize.restype = None

        self.type: str = self._lib.model_name().decode()
        self.name: str = instance if instance is not None else self.type
        self.order: int = order if order is not None else self._lib.model_order()
        self.update_rate: float = update_rate if update_rate is not None else self._lib.model_update_rate()
        self.stop_time: float = stop_time if stop_time is not None else self._lib.model_stop_time()
        self.dt: float = 1.0 / self.update_rate if self.update_rate > 0 else None
        self.steps: int = 0  # number of model_update() calls so far
        self.params: dict = params if params is not None else {}

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

    Timing convention:
      model_initialize() establishes each model's state at t = 0.
      model_update(t) brings the model's state from its previous update to t,
      so a model at rate r is first updated at t = 1/r, then 2/r, ... up to and
      including the run duration. Between updates its published values hold.

    Per-model stop_time:
      A model with stop_time >= 0 stops being updated once sim_time reaches
      that value. model_finalize() is still called for it at sim end.

    Loggers:
      Registered loggers (see loggers/) are notified after initialization,
      after every model update, after every frame (all updates sharing one
      sim_time have run), and after finalization.
    """

    def __init__(self) -> None:
        self.bus = MessageBus(ctypes.CDLL(BUS_LIB, mode=ctypes.RTLD_GLOBAL))  # must precede model loads
        self._heap: list[tuple[float, Model]] = []
        self.sim_time: float = 0.0
        self.duration: float = 0.0
        self.models: list[Model] = []
        self.loggers: list = []

    def add_model(self, model: Model) -> None:
        """Register a Model instance with the scheduler."""
        self.models.append(model)

    def add_logger(self, logger) -> None:
        """Register a logger (see loggers/) to be notified at lifecycle points."""
        self.loggers.append(logger)

    def load_model(self, lib_path: str, order=None, update_rate=None, stop_time=None,
                   params=None, instance=None) -> Model:
        """Load a shared library, wrap it as a Model, and register it."""
        model = Model(lib_path, order=order, update_rate=update_rate, stop_time=stop_time,
                      params=params, instance=instance)
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
            self._schedule_next(model)
        for logger in self.loggers:
            logger.on_initialize(self)

    def _step(self) -> None:
        next_time, model = heapq.heappop(self._heap)
        self.sim_time = next_time
        model.update(self.sim_time)
        for logger in self.loggers:
            logger.on_step(self, model)
        model.steps += 1
        self._schedule_next(model)

    def _schedule_next(self, model: Model) -> None:
        if model.update_rate <= 0:  # rate 0 = not clock-driven, never scheduled
            return
        # Compute from the step count rather than accumulating dt, so models at
        # different rates land on bit-identical times (e.g. 6/100 == 3/50)
        next_scheduled = (model.steps + 1) / model.update_rate
        # Queue only if the model's stop_time has not been reached
        if model.stop_time < 0.0 or next_scheduled <= model.stop_time:
            heapq.heappush(self._heap, (next_scheduled, model))

    def _finalize(self) -> None:
        for model in self.models:
            model.finalize()
        for logger in self.loggers:
            logger.on_finalize(self)

    def run(self, duration: float) -> None:
        """Run the full simulation lifecycle for the given duration (seconds)."""
        self.duration = duration
        self._initialize()
        while self._heap and self._heap[0][0] <= duration:
            self._step()
            # A frame ends once no other model is scheduled at this same sim_time
            if not self._heap or self._heap[0][0] > self.sim_time:
                for logger in self.loggers:
                    logger.on_frame(self)
        self._finalize()
