set(MODEL_OUTPUT_DIR ${CMAKE_SOURCE_DIR}/build/models)

# Each model is built as a shared library, loaded at runtime by the Python scheduler.
# Use: add_model(<name> <sources...>)
function(add_model name)
    add_library(${name} SHARED ${ARGN})
    target_include_directories(${name} PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_SOURCE_DIR}/src/message_bus
    )
    target_link_libraries(${name} PRIVATE message_bus)
    set_target_properties(${name} PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY ${MODEL_OUTPUT_DIR}
        PREFIX ""  # output as <name>.so, not lib<name>.so
    )
endfunction()

# ---------- Register models below ----------
add_model(example_model example_model.cpp)
add_model(hello_world hello_world.cpp)
