# hello_world.py
#
# Python-side configuration for the hello_world model.
# Every C++ model has a matching .py file here that defines how the scheduler
# should treat it. The values here override whatever the C++ functions return,
# making this file the single source of truth for scheduling behavior.
#
# A scenario imports this file to read these values before loading the model.

# CHANGE THIS: initialization order (must match intent in the .cpp file).
# Lower numbers initialize and run first.
order       = 1

# CHANGE THIS: how many times per second model_update() is called.
update_rate = 1.0   # Hz

# CHANGE THIS: stop calling model_update() after this many seconds.
# Set to -1.0 to run until the scenario ends.
stop_time   = -1.0

# CHANGE THIS: input parameters passed to the model before initialization.
# Add key-value pairs here for any tuneable constants your model needs
# (e.g., initial conditions, physical properties, configuration flags).
# Leave as an empty dict {} if the model needs no external inputs.
params      = {}
