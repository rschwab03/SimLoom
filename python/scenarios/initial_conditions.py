# initial_conditions.py  (scenario)
#
# Runs example_model and records its initial conditions to a JSON file.
# Use this file as a template for adding logging to a scenario.
#
# Loggers are configured entirely from Python: adding a new signal to the log
# only means editing this file, with no C++ rebuild needed.
#
# Run from the python/ directory:
#   python3 scenarios/initial_conditions.py

# --- BOILERPLATE: make the parent directory importable.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scheduler import Scheduler
from loggers import InitialConditionLogger

import models.example_model as cfg

# --- BOILERPLATE: paths to the compiled models and the run output directory.
ROOT_DIR   = os.path.join(os.path.dirname(__file__), "..", "..")
BUILD_DIR  = os.path.join(ROOT_DIR, "build", "models")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "initial_conditions")

sched = Scheduler()

sched.load_model(
    os.path.join(BUILD_DIR, "example_model.so"),
    order=cfg.order,
    update_rate=cfg.update_rate,
    stop_time=cfg.stop_time,
    params=cfg.params,
)

# CHANGE THIS: choose what to record once, right after every model has initialized.
#   add()       - a message bus key, or a glob like "example/*"
#   add_value() - any Python-side constant (numbers, strings, dicts, lists)
ic_log = InitialConditionLogger(os.path.join(OUTPUT_DIR, "ic.json"))
ic_log.add("example/*")
ic_log.add_value("description", "example_model baseline run")
sched.add_logger(ic_log)

# CHANGE THIS: total simulation time to run, in seconds.
sched.run(duration=0.05)

print(f"\nInitial conditions written to {os.path.normpath(ic_log.path)}")
