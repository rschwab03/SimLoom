#include "model_interface.hpp"
#include "message_bus.hpp"
#include <cstdio>

extern "C" {

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
    MessageBus::instance().publish("example/counter", 0.0);
    printf("[%s] initialize  counter = 0\n", model_name());
}

void model_update(double sim_time) {
    double counter = MessageBus::instance().get("example/counter") + 1.0;
    MessageBus::instance().publish("example/counter", counter);
    printf("[%s] update  t = %.6f s  counter = %.0f\n", model_name(), sim_time, counter);
}

void model_finalize() {
    printf("[%s] finalize  counter = %.0f\n", model_name(),
           MessageBus::instance().get("example/counter"));
}

} // extern "C"
