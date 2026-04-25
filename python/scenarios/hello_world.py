# hello_world.py  (scenario)
#
# A standalone script that runs only the hello_world model for 5 seconds.
# Use this file as a template when building new scenarios.
#
# A scenario is the top-level entry point for a simulation run. It decides:
#   - which models to load
#   - how long to run
# The scheduler handles everything else: initialization order, timing, finalization.
#
# Run from the python/ directory:
#   python3 scenarios/hello_world.py

# --- BOILERPLATE: make the parent directory importable so we can find
# scheduler.py and the models/ package regardless of where this script is run from.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scheduler import Scheduler

# Import the Python config for each model this scenario uses.
# "cfg" gives us the scheduling parameters (order, update_rate, stop_time).
import models.hello_world as cfg

# --- BOILERPLATE: path to the compiled model libraries.
# CMake places all .so files here after a successful build.
BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "build", "models")

# --- BOILERPLATE: create the scheduler.
# This also loads the message bus, which must happen before any model is loaded.
sched = Scheduler()

# Load each model the scenario needs.
# Pass the scheduling parameters from the Python config file so that this file
# (not the compiled C++) is the authoritative source for how the model runs.
# CHANGE THIS: add one sched.load_model() call per model your scenario uses.
sched.load_model(
    os.path.join(BUILD_DIR, "hello_world.so"),
    order=cfg.order,
    update_rate=cfg.update_rate,
    stop_time=cfg.stop_time,
)

# --- BOILERPLATE: print the model registry so it's easy to confirm
# which models are loaded and at what rates before the run begins.
print(f"Loaded {len(sched.models)} model(s):")
for m in sorted(sched.models, key=lambda m: m.order):
    stop = f"{m.stop_time:.3f} s" if m.stop_time >= 0 else "sim end"
    print(f"  [{m.order:3d}] {m.name:30s}  {m.update_rate} Hz  stop={stop}")
print()

# CHANGE THIS: total wall-clock simulation time to run, in seconds.
sched.run(duration=5.0)
