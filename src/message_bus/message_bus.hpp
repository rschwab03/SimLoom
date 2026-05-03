#pragma once

/**
 * @file message_bus.hpp
 * @brief Shared signal store for inter-model communication.
 *
 * All models share a single MessageBus singleton. Signals are keyed by
 * strings following the convention `"subsystem/signal_name"` (e.g.,
 * `"nav/altitude"`, `"guidance/commanded_az"`).
 *
 * The message_bus shared library must be loaded with RTLD_GLOBAL before any
 * model libraries so that all models reference the same singleton instance.
 */

#include <string>
#include <unordered_map>

class MessageBus {
public:
    /// Returns the process-wide singleton instance.
    static MessageBus& instance();

    /// Publish @p value under @p key, overwriting any previous value.
    void publish(const std::string& key, double value);

    /**
     * @brief Retrieve the value stored under @p key.
     * @param key          Signal key in `"subsystem/signal_name"` format.
     * @param default_val  Returned when the key has not been published.
     * @return The stored value, or @p default_val if absent.
     */
    double get(const std::string& key, double default_val = 0.0) const;

    /// Returns true if @p key has been published at least once.
    bool has(const std::string& key) const;

    /// Removes all signals. Typically called between simulation runs.
    void reset();

private:
    MessageBus() = default;
    std::unordered_map<std::string, double> signals_;
};
