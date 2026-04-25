# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A 6DOF simulation of a missile/interceptor. C++ implements the physics models; Python drives the simulation lifecycle via a scheduler.

## Build

```bash
cmake -B build
cmake --build build
```

Model shared libraries are placed in `build/models/`.

## Running

```bash
cd python
python main.py
```

## Architecture

### C++ Models (`src/models/`)

Each model is compiled as a separate shared library (`.so`) and must implement the functions declared in `src/models/model_interface.hpp`:

| Function | Description |
|---|---|
| `model_name()` | String identifier |
| `model_update_rate()` | Execution rate in Hz |
| `model_order()` | Initialization order (ascending) |
| `model_stop_time()` | Stop time in seconds; `-1.0` = run until sim ends |
| `model_initialize()` | Called once before the sim loop, in `model_order` sequence |
| `model_update(double sim_time)` | Called each scheduled time step |
| `model_finalize()` | Called once after the sim loop for all models |

To add a new model:
1. Create `src/models/<name>.cpp` implementing all interface functions
2. Add `add_model(<name> <name>.cpp)` to `src/models/CMakeLists.txt`
3. Create `python/models/<name>.py` with the model's input `params` dict

### Python Models (`python/models/`)

Each C++ model has a matching `.py` file (same name) that specifies its input parameters. These are loaded by the scheduler and passed to the C++ model before initialization.

### Python Scheduler (`python/scheduler.py`)

- **`Model`** — wraps a `.so` via `ctypes`; exposes `name`, `update_rate`, `dt`, `order`, `stop_time`
- **`Scheduler`** — manages the full sim lifecycle:
  1. `_initialize()` — calls `model_initialize()` on all models sorted by `order`, then pushes all onto a min-heap at `t=0`
  2. Event loop — pops `(next_time, model)`, calls `model_update()`, re-queues at `next_time + dt` unless `stop_time` has been reached
  3. `_finalize()` — calls `model_finalize()` on all models

`main.py` is the entry point: discovers `.so` files in `build/models/`, prints the model registry, and calls `sched.run(duration)`.

## Message Bus

A shared signal store (`src/message_bus/`) compiled as `build/message_bus.so`. All models can exchange data through it without direct linkage.

**API** (`#include "message_bus.hpp"`):
```cpp
MessageBus::instance().publish("subsystem/signal_name", value);
double v = MessageBus::instance().get("subsystem/signal_name", default_val);
bool exists  = MessageBus::instance().has("subsystem/signal_name");
MessageBus::instance().reset(); // clears all signals
```

**Key convention:** `"subsystem/signal_name"` (e.g., `"nav/altitude"`, `"guidance/commanded_az"`).

**Loading order:** `Scheduler.__init__` loads `message_bus.so` with `RTLD_GLOBAL` before any model `.so` files. This ensures all models share the same singleton instance — without `RTLD_GLOBAL` each `.so` would get its own copy.

## Scenarios

`python/scenarios/` contains standalone runnable scripts that selectively load models and set a simulation duration. Unlike `main.py` (which auto-discovers all models), each scenario explicitly loads only the models it needs and configures them via the matching `python/models/<name>.py` config.

```bash
cd python
python3 scenarios/hello_world.py
```
