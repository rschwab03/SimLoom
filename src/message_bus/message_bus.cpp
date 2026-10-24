#include "message_bus.hpp"

#include <cstring>

MessageBus& MessageBus::instance() {
    static MessageBus inst;
    return inst;
}

void MessageBus::publish(const std::string& key, double value) {
    signals_[key] = value;
}

double MessageBus::get(const std::string& key, double default_val) const {
    auto it = signals_.find(key);
    return it != signals_.end() ? it->second : default_val;
}

bool MessageBus::has(const std::string& key) const {
    return signals_.count(key) > 0;
}

std::vector<std::string> MessageBus::keys() const {
    std::vector<std::string> out;
    out.reserve(signals_.size());
    for (const auto& kv : signals_) out.push_back(kv.first);
    return out;
}

void MessageBus::reset() {
    signals_.clear();
}

extern "C" {

double bus_get(const char* key, double default_val) {
    return MessageBus::instance().get(key, default_val);
}

int bus_has(const char* key) {
    return MessageBus::instance().has(key) ? 1 : 0;
}

void bus_publish(const char* key, double value) {
    MessageBus::instance().publish(key, value);
}

size_t bus_keys(char* buf, size_t buflen) {
    std::string joined;
    for (const auto& k : MessageBus::instance().keys()) {
        if (!joined.empty()) joined += '\n';
        joined += k;
    }
    if (buf && buflen > 0) {
        size_t n = joined.size() < buflen - 1 ? joined.size() : buflen - 1;
        std::memcpy(buf, joined.data(), n);
        buf[n] = '\0';
    }
    return joined.size();
}

} // extern "C"
