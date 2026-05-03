# SimLoom

SimLoom is a framework for building simulations out of independently compiled C++ models orchestrated by a Python scheduler. It is not specific to any domain — the same architecture works whether you are simulating physical systems, financial markets, logistics networks, or anything else that evolves over time.

---

## The core idea

A simulation is a program that advances some model of the world forward in time, step by step. The challenge is that real systems are made of many interacting subsystems, each with its own update frequency, its own inputs, and its own outputs. A navigation algorithm might need to run at 100 Hz while a logging subsystem only needs to run at 1 Hz. A sensor model produces data that a control law consumes, but neither should need to know how the other is implemented.

SimLoom solves this with three components that each have one job:

- **C++ models** — implement the physics, logic, or behavior of one subsystem each
- **A message bus** — lets models exchange data without knowing about each other
- **A Python scheduler** — loads models, wires them together, and drives the time loop

---

## Why C++ for models, Python for the scheduler?

C++ is fast and gives you direct control over numerics — important for models that run thousands of times per second. Python is slow for tight loops but excellent for configuration, file I/O, and gluing things together.

SimLoom splits the work along that boundary. Each C++ model is compiled into a shared library (a `.so` file), and the Python scheduler loads them at runtime using `ctypes`. Python never calls into a model's inner loop directly — it hands off to compiled code for each update. This means you get C++ performance where it matters and Python flexibility everywhere else.

A secondary benefit is that models are independently compiled. Adding a new model does not require recompiling existing ones. You can also load a different set of models for different experiments without changing any model code.

---

## The model interface

Every model exposes seven plain-C functions with identical signatures:

```cpp
const char* model_name();        // unique string identifier
double      model_update_rate(); // how often to call model_update(), in Hz
int         model_order();       // initialization sequence (ascending)
double      model_stop_time();   // stop updating after this many seconds; -1 = run to end
void        model_initialize();  // called once before the sim loop
void        model_update(double sim_time); // called each time step
void        model_finalize();    // called once after the sim loop
```

The interface is deliberately narrow. The scheduler only needs to know three things about a model: when to start it, how often to call it, and when to stop. Everything else is the model's private concern.

The functions use C linkage (`extern "C"`) so that Python's `ctypes` library can find them by name. C++ normally "mangles" function names during compilation to encode type information; `extern "C"` suppresses that, keeping the names predictable.

---

## The message bus

Models need to share data — a sensor model produces a measurement that a control law model consumes. The naive approach is to have them call each other's functions directly, but that creates a dependency graph that quickly becomes unmanageable.

SimLoom instead uses a message bus: a global key–value store where every signal is a string key mapped to a `double` value.

```cpp
// Producer
MessageBus::instance().publish("nav/altitude", 1500.0);

// Consumer (in a different model, with no include or link dependency on the producer)
double alt = MessageBus::instance().get("nav/altitude", 0.0);
```

Any model can publish to any key and read from any key. Models are completely decoupled — you can add, remove, or swap a model without modifying the models around it, as long as the signals it produces or consumes remain consistent.

The bus only stores `double` values. This is a deliberate constraint. It keeps the interface simple and avoids the need for shared struct definitions across model boundaries. Composite quantities (a 3D vector, a quaternion) are split into named scalar signals.

### Why a singleton loaded with RTLD_GLOBAL

The message bus is a singleton — there is exactly one instance per process. But because each model is a separate `.so` file, the operating system would normally give each one its own copy of any static data it defines. SimLoom avoids this by loading `message_bus.so` with the `RTLD_GLOBAL` flag before any model is loaded. This makes the bus's symbols visible to every subsequently loaded library, so they all resolve to the same instance.

---

## The scheduler

The scheduler is responsible for one thing: calling `model_update()` on the right model at the right simulation time.

### Multi-rate execution

Different models run at different frequencies. Rather than running everything at the fastest rate (which would waste cycles calling slow models too often) or the slowest rate (which would under-sample fast models), SimLoom uses an event-driven approach with a min-heap.

Each model has a scheduled next-fire time. The scheduler always pops the model with the smallest next-fire time, calls its `model_update()`, and re-queues it at `current_time + 1/update_rate`. This naturally handles any combination of update rates without a fixed global timestep.

```
heap: [(0.0, model_A_100Hz), (0.0, model_B_1Hz)]

pop model_A → update at t=0.000 → re-queue at t=0.010
pop model_A → update at t=0.010 → re-queue at t=0.020
...
pop model_B → update at t=0.000 → re-queue at t=1.000  (interleaved naturally)
```

### Lifecycle

The full simulation lifecycle is:

1. **Initialize** — call `model_initialize()` on all models in ascending `model_order()` sequence. Order matters when one model's initialization depends on another's output.
2. **Event loop** — repeatedly pop the earliest-scheduled model, call `model_update()`, re-queue. Stop when the heap is empty or the scheduled time reaches the scenario duration.
3. **Finalize** — call `model_finalize()` on all models, regardless of their individual stop times.

---

## Scenarios

`python/scenarios/` contains standalone scripts that each define one simulation run. A scenario decides which models to load and for how long to run. It does not need to know anything about model internals.

```python
sched = Scheduler()
sched.load_model("build/models/nav.so",      order=0, update_rate=100.0)
sched.load_model("build/models/guidance.so", order=1, update_rate=50.0)
sched.run(duration=30.0)
```

This is in contrast to `main.py`, which auto-discovers every `.so` in the build directory. Scenarios are the right choice when you want explicit control over which models participate in a run.

---

## Project layout

```
SimLoom/
├── src/
│   ├── message_bus/        # shared signal store (compiled to message_bus.so)
│   └── models/             # one .cpp per model (each compiled to its own .so)
│       └── model_interface.hpp   # the seven-function contract every model implements
├── python/
│   ├── scheduler.py        # Model wrapper + Scheduler event loop
│   ├── main.py             # auto-discovers all .so files and runs them
│   ├── models/             # per-model Python config (order, update_rate, stop_time, params)
│   └── scenarios/          # standalone run scripts
├── build/                  # CMake output (ignored by git)
│   ├── message_bus.so
│   └── models/
├── docs/                   # Doxygen output (ignored by git)
├── build.sh                # configure + compile
├── docs.sh                 # configure + generate HTML docs
└── Doxyfile                # Doxygen configuration
```

---

## Adding a new model

1. Create `src/models/<name>.cpp` implementing all seven interface functions.
2. Add `add_model(<name> <name>.cpp)` to `src/models/CMakeLists.txt`.
3. Create `python/models/<name>.py` with `order`, `update_rate`, `stop_time`, and `params`.
4. Run `./build.sh`.
5. Load the model in a scenario or let `main.py` discover it automatically.

The `hello_world` model in `src/models/hello_world.cpp` is a fully annotated template — copy it as a starting point.

---

## Building

```bash
./build.sh          # compile all models
./docs.sh           # generate HTML documentation → docs/html/index.html
```
