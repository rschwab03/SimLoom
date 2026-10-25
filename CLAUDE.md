# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An asynchronous, multi-rate simulation framework. C++ implements the models, passing data through a pub/sub message bus; Python sets input parameters, orchestrates scenarios, and drives the simulation lifecycle via a scheduler. SimLoom is domain-agnostic — do not add references to specific simulation domains (aerospace, finance, etc.) in shared framework code.

## Commands

```bash
./build.sh                        # configure + compile all models
./docs.sh                         # generate HTML docs → docs/html/index.html

cd python
python main.py                    # run all discovered models for 50 ms
python3 scenarios/hello_world.py  # run a single scenario
```

## Architecture

### Key invariant: message bus loading order

`Scheduler.__init__` loads `message_bus.so` with `RTLD_GLOBAL` **before** any model `.so`. This is what gives all models a shared singleton — without `RTLD_GLOBAL` each `.so` gets its own copy. Never reorder this.

### C++ Models (`src/models/`)

Each model is a separate shared library implementing the seven required functions in `model_interface.hpp`, plus the optional `model_set_instance(const char*)`. The CMake helper `add_model(<name> <name>.cpp)` in `src/models/CMakeLists.txt` handles build configuration. Output lands in `build/models/<name>.so` (no `lib` prefix).

To add a new model:
1. Create `src/models/<name>.cpp` implementing all interface functions (`hello_world.cpp` is the annotated template)
2. Add `add_model(<name> <name>.cpp)` to `src/models/CMakeLists.txt`
3. Create `python/models/<name>.py` with `order`, `update_rate`, `stop_time`, and `params`

**Instances:** `load_model(path, instance="name")` copies the `.so` into a temp directory and loads the copy, so each instance has its own static state. The copy must be a real copy, not a link, because glibc matches already-loaded libraries by inode. The copies live until the process exits. The name is passed to `model_set_instance()` before any other call, and models should use it as their bus key prefix (see `example_model.cpp`). `Model.name` is the instance name, and `Model.type` is what `model_name()` returns.

**Not clock-driven:** an `update_rate` of `0` means the model is initialized and finalized but never scheduled for `model_update()`.

### Python Models (`python/models/`)

Each `.py` config file is the authoritative source for a model's scheduling parameters — the values here override whatever the C++ functions return. The `params` dict is a placeholder for future parameter-passing; it is not yet consumed by the scheduler.

### Scheduler (`python/scheduler.py`)

Multi-rate event loop built on a min-heap. Each tick pops the earliest `(next_time, model)` pair, calls `model_update(sim_time)`, and re-queues at `(steps + 1) / update_rate`. That time is computed from the step count, never by accumulating `dt`, so models at different rates hit bit-identical times. **Timing convention:** `model_initialize()` sets the state at t=0, and `model_update(t)` brings the state *to* t. The first update is at t=1/rate, never at t=0, and the loop includes t=duration. Published values hold between a model's updates. The time-series logger samples once at initialize, which gives t=0, then at the end of each frame. A model with `stop_time >= 0` stops being updated once `sim_time` reaches that value; `model_finalize()` is still called for it at sim end.

### Scenarios (`python/scenarios/`)

Standalone scripts that explicitly load only the models they need. Prefer scenarios over `main.py` when you want a controlled, reproducible run with a specific model subset.

## Message Bus

```cpp
#include "message_bus.hpp"
MessageBus::instance().publish("subsystem/signal", value);
double v = MessageBus::instance().get("subsystem/signal", default_val);
bool   e = MessageBus::instance().has("subsystem/signal");
MessageBus::instance().reset();
```

Key convention: `"subsystem/signal_name"`. All signals are `double`.

## Logging (`python/loggers/`)

Loggers are configured from Python, so recording a new signal needs no C++ rebuild. They read the bus through the `extern "C"` API in `message_bus.hpp` (`bus_get`, `bus_has`, `bus_publish`, `bus_keys`), wrapped by `python/bus.py` and exposed as `Scheduler.bus`.

```python
from loggers import InitialConditionLogger, TimeSeriesLogger
log = InitialConditionLogger("output/run/ic.json")
log.add("example/*")              # bus key or glob
log.add_value("note", "baseline") # any JSON-serialisable Python value
sched.add_logger(log)
sched.add_logger(TimeSeriesLogger("output/run/ts.json", rate=None, csv=True).add("example/*"))
```

The scheduler calls:
- `on_initialize(sched)` after all `model_initialize()` calls
- `on_step(sched, model)` after each `model_update()`
- `on_frame(sched)` once every update at the current `sim_time` has run
- `on_finalize(sched)` after all `model_finalize()` calls

Sample state in `on_frame`, not `on_step`: mid-frame the bus can be only partly updated. To add a new logger type, subclass `loggers.base.Logger` and override the hooks it needs.

- `InitialConditionLogger` writes `{"run", "signals", "values"}` once, at initialize.
- `TimeSeriesLogger` samples in `on_frame`, either every frame or at `rate` Hz. At finalize it writes column-oriented JSON `{"run", "values", "t": [...], "signals": {key: [...]}}`. It resolves patterns at the first sample.
- `python3 -m loggers <file.json>` (or `json_to_csv`) converts time-series JSON to CSV.

Output goes under `output/` (gitignored).

## Documentation

Doxygen is configured via `Doxyfile`. Each model's `.cpp` should include a `@file` MDR block — see `hello_world.cpp` for the template. MDR sections (Model Descriptions and Reports) cover: overview, message bus inputs, message bus outputs, block diagram position, and verification evidence.
