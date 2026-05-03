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

Each model is a separate shared library implementing the seven functions in `model_interface.hpp`. The CMake helper `add_model(<name> <name>.cpp)` in `src/models/CMakeLists.txt` handles build configuration. Output lands in `build/models/<name>.so` (no `lib` prefix).

To add a new model:
1. Create `src/models/<name>.cpp` implementing all interface functions (`hello_world.cpp` is the annotated template)
2. Add `add_model(<name> <name>.cpp)` to `src/models/CMakeLists.txt`
3. Create `python/models/<name>.py` with `order`, `update_rate`, `stop_time`, and `params`

### Python Models (`python/models/`)

Each `.py` config file is the authoritative source for a model's scheduling parameters — the values here override whatever the C++ functions return. The `params` dict is a placeholder for future parameter-passing; it is not yet consumed by the scheduler.

### Scheduler (`python/scheduler.py`)

Multi-rate event loop built on a min-heap. Each tick pops the earliest `(next_time, model)` pair, calls `model_update(sim_time)`, and re-queues at `next_time + dt`. A model with `stop_time >= 0` stops being updated once `sim_time` reaches that value; `model_finalize()` is still called for it at sim end.

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

## Documentation

Doxygen is configured via `Doxyfile`. Each model's `.cpp` should include a `@file` MDR block — see `hello_world.cpp` for the template. MDR sections (Model Descriptions and Reports) cover: overview, message bus inputs, message bus outputs, block diagram position, and verification evidence.
