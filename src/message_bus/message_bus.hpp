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

#include <cstddef>
#include <string>
#include <unordered_map>
#include <vector>

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

    /// Returns every key that has been published, in unspecified order.
    std::vector<std::string> keys() const;

    /// Removes all signals. Typically called between simulation runs.
    void reset();

private:
    MessageBus() = default;
    std::unordered_map<std::string, double> signals_;
};

/**
 * @name C API
 * @brief Plain-C access to the singleton so Python (ctypes) can read and
 * write signals without any model-specific code. Used by the Python loggers.
 */
///@{
extern "C" {

/// Equivalent to `MessageBus::instance().get(key, default_val)`.
double bus_get(const char* key, double default_val);

/// Returns 1 if @p key has been published, 0 otherwise.
int bus_has(const char* key);

/// Equivalent to `MessageBus::instance().publish(key, value)`.
void bus_publish(const char* key, double value);

/**
 * @brief Write all published keys into @p buf, separated by `'\n'`.
 * @param buf     Destination buffer (may be null when @p buflen is 0).
 * @param buflen  Size of @p buf in bytes.
 * @return Number of bytes required, excluding the null terminator. If this is
 *         >= @p buflen the output was truncated; call again with a larger buffer.
 */
size_t bus_keys(char* buf, size_t buflen);

} // extern "C"
///@}
