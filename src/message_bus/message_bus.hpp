#pragma once
#include <string>
#include <unordered_map>

class MessageBus {
public:
    static MessageBus& instance();
    void   publish(const std::string& key, double value);
    double get(const std::string& key, double default_val = 0.0) const;
    bool   has(const std::string& key) const;
    void   reset();
private:
    MessageBus() = default;
    std::unordered_map<std::string, double> signals_;
};
