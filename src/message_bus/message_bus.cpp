#include "message_bus.hpp"

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

void MessageBus::reset() {
    signals_.clear();
}
