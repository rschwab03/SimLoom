# time_series.py  (scenario)
#
# Runs three instances of example_model and records both their initial
# conditions and the time history of their signals. Use this file as a
# template for logging a multi-model scenario.
#
#   fast    100 Hz       counter climbs every 10 ms
#   slow     25 Hz       counter climbs every 40 ms
#   static   0 Hz        initialized only; never updated. Stands in for a model
#                        that would update only when a signal it subscribes to
#                        changes, and here it subscribes to nothing.
#
# Each instance is an independent copy of example_model.so, with its own state,
# and publishes under its own key prefix (fast/counter, slow/counter, ...).
#
# Loggers are configured entirely from Python: adding a new signal to the log
# only means editing this file, with no C++ rebuild needed.
#
# Run from the python/ directory:
#   python3 scenarios/time_series.py

# --- BOILERPLATE: make the parent directory importable.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scheduler import Scheduler
from loggers import InitialConditionLogger, TimeSeriesLogger

import models.example_model as cfg

# --- BOILERPLATE: paths to the compiled models and the run output directory.
ROOT_DIR   = os.path.join(os.path.dirname(__file__), "..", "..")
BUILD_DIR  = os.path.join(ROOT_DIR, "build", "models")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "time_series")

sched = Scheduler()

# CHANGE THIS: one load_model() call per instance. `instance` must be unique;
# it names the model and prefixes its bus keys. update_rate=0.0 means the model
# is never scheduled for model_update().
for instance, update_rate in [("fast", 100.0), ("slow", 25.0), ("static", 0.0)]:
    sched.load_model(
        os.path.join(BUILD_DIR, "example_model.so"),
        instance=instance,
        order=cfg.order,
        update_rate=update_rate,
        stop_time=cfg.stop_time,
        params=cfg.params,
    )

# --- BOILERPLATE: print the model registry.
print(f"Loaded {len(sched.models)} model(s):")
for m in sorted(sched.models, key=lambda m: m.order):
    stop = f"{m.stop_time:.3f} s" if m.stop_time >= 0 else "sim end"
    rate = f"{m.update_rate} Hz" if m.update_rate > 0 else "not clocked"
    print(f"  [{m.order:3d}] {m.name:30s}  {rate}  stop={stop}")
print()

# CHANGE THIS: signals recorded once, right after every model has initialized.
ic_log = InitialConditionLogger(os.path.join(OUTPUT_DIR, "ic.json"))
ic_log.add("*/counter")
sched.add_logger(ic_log)

# CHANGE THIS: signals recorded over time.
#   rate=None   - sample every frame (every time any model updates)
#   rate=<Hz>   - sample at a fixed rate instead
#   csv=True    - also write a .csv next to the .json
ts_log = TimeSeriesLogger(os.path.join(OUTPUT_DIR, "time_series.json"), rate=None, csv=True)
ts_log.add("fast/counter").add("slow/counter").add("static/counter")
sched.add_logger(ts_log)

# CHANGE THIS: total simulation time to run, in seconds.
sched.run(duration=0.1)

print(f"\nLogs written to {os.path.normpath(OUTPUT_DIR)}")
