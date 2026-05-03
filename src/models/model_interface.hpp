#pragma once

/**
 * @file model_interface.hpp
 * @brief Contract every C++ model shared library must implement.
 *
 * Build each model as a separate shared library; the Python scheduler loads
 * them at runtime and calls these functions. All symbols must be exported
 * with C linkage so ctypes can resolve them by name.
 */

extern "C" {

/// Human-readable model identifier. Must be unique across all loaded models.
const char* model_name();

/// Desired execution rate in Hz. The scheduler calls model_update() at this frequency.
double model_update_rate();

/**
 * @brief Initialization order relative to other models.
 *
 * Models are initialized in ascending order. Use this to ensure models that
 * produce outputs run before models that depend on those outputs.
 */
int model_order();

/**
 * @brief Simulation time (seconds) at which this model stops being updated.
 *
 * Return -1.0 to run until the simulation ends. model_finalize() is still
 * called for the model regardless of its stop time.
 */
double model_stop_time();

/**
 * @brief Called once before the simulation loop, in model_order() sequence.
 *
 * Use this to allocate resources, publish initial signal values to the
 * message bus, or set up any state the model needs before updates begin.
 */
void model_initialize();

/**
 * @brief Called each scheduled time step at model_update_rate() Hz.
 * @param sim_time Current simulation time in seconds.
 *
 * This is where the model's core logic executes each frame. Read inputs from
 * the message bus, compute outputs, and publish results back to the bus.
 */
void model_update(double sim_time);

/**
 * @brief Called once after the simulation loop ends.
 *
 * Called for all models regardless of stop_time. Use this to write output
 * files, free resources, or print summary statistics.
 */
void model_finalize();

} // extern "C"
