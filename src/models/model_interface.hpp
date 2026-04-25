#pragma once

// Every C++ model must implement these extern "C" functions.
// Build each model as a shared library; the Python scheduler loads and calls them.

extern "C" {

// Human-readable model identifier
const char* model_name();

// Desired execution rate in Hz
double model_update_rate();

// Initialization order — models are initialized in ascending order
int model_order();

// Simulation time (seconds) at which this model stops being updated.
// Return -1.0 to run until the simulation ends.
double model_stop_time();

// Called once before the simulation loop, in model_order() sequence
void model_initialize();

// Called each scheduled time step; sim_time is current simulation time in seconds
void model_update(double sim_time);

// Called once after the simulation loop ends (for all models, regardless of stop_time)
void model_finalize();

} // extern "C"
