# Python-side configuration for example_model.so
#
# These values override whatever the C++ functions return.

order       = 0
update_rate = 100.0  # Hz
stop_time   = -1.0   # run until the scenario ends

# Input parameters for the model. The parameter names here should mirror the
# inputs expected by the C++ model.
params = {
}
