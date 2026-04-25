add_library(message_bus SHARED message_bus.cpp)
target_include_directories(message_bus PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
set_target_properties(message_bus PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/build
    PREFIX ""
)
