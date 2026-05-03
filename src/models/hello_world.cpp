// hello_world.cpp
//
// A minimal example model that demonstrates the full simulation lifecycle.
// Use this file as a template when creating new models.
//
// Every model is compiled into its own shared library (.so file) that the
// Python scheduler loads and calls at runtime. The scheduler doesn't care
// what the model does internally — it only requires that each model expose
// the six functions below with exactly these names and signatures.

// --- BOILERPLATE: always include this for printf ---
#include <cstdio>

// --- BOILERPLATE: extern "C" tells the compiler to export these functions
// with plain C-style names so Python's ctypes can find them by name.
// Without this, C++ would mangle the names and ctypes would fail to load them.
extern "C" {

// --------------------------------------------------------------------------
// MODEL METADATA
// These four functions tell the scheduler how to treat this model.
// They are called once at startup — return a constant value from each.
// --------------------------------------------------------------------------

// CHANGE THIS: return a unique string identifier for your model.
//! [model_metadata]
const char* model_name()        { return "hello_world"; }

// CHANGE THIS: how many times per second model_update() should be called.
// 1.0 Hz = once per second, 100.0 Hz = 100 times per second, etc.
double      model_update_rate() { return 1.0; }

// CHANGE THIS: initialization order relative to other models.
// Lower numbers initialize first. Use this to ensure models that produce
// outputs run before models that depend on those outputs.
int         model_order()       { return 1; }

// CHANGE THIS: simulation time (seconds) at which to stop calling model_update().
// Use -1.0 to run for the full duration of the scenario.
double      model_stop_time()   { return -1.0; }
//! [model_metadata]

// --------------------------------------------------------------------------
// LIFECYCLE FUNCTIONS
// The scheduler calls these in order: initialize → update (repeatedly) → finalize
// --------------------------------------------------------------------------

// Called once, before the simulation loop begins.
// Use this to allocate memory, open files, set initial conditions, etc.
// Models are initialized in ascending model_order() sequence.
//! [model_lifecycle]
void model_initialize() {
    printf("Hello World!\n");
}

// Called once per time step, at the rate defined by model_update_rate().
// sim_time is the current simulation time in seconds.
// This is where the model's physics/math executes each frame.
void model_update(double sim_time) {
    printf("sim_time = %f s\n", sim_time);
}

// Called once, after the simulation loop ends (even if the scenario is cut short).
// Use this to write output files, free memory, print summary statistics, etc.
void model_finalize() {
    printf("So Long, and Thanks for All the Fish!\n");
}
//! [model_lifecycle]

} // extern "C"  --- BOILERPLATE: must close the extern "C" block
