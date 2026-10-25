#include "model_interface.hpp"
#include "message_bus.hpp"
#include <cstdio>
#include <string>

// Instance name; also the bus key prefix. Defaults to "example" when the model
// is loaded without an instance name.
static std::string g_instance = "example";

static std::string counter_key() { return g_instance + "/counter"; }

extern "C" {

void model_set_instance(const char* name) {
    g_instance = name;
}

const char* model_name() {
    return "example_model";
}

double model_update_rate() {
    return 100.0; // Hz
}

int model_order() {
    return 0;
}

double model_stop_time() {
    return -1.0; // run until simulation ends
}

void model_initialize() {
    MessageBus::instance().publish(counter_key(), 0.0);
    printf("[%s] initialize  counter = 0\n", g_instance.c_str());
}

void model_update(double sim_time) {
    double counter = MessageBus::instance().get(counter_key()) + 1.0;
    MessageBus::instance().publish(counter_key(), counter);
    printf("[%s] update  t = %.6f s  counter = %.0f\n", g_instance.c_str(), sim_time, counter);
}

void model_finalize() {
    printf("[%s] finalize  counter = %.0f\n", g_instance.c_str(),
           MessageBus::instance().get(counter_key()));
}

} // extern "C"
