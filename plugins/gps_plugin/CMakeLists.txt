file(GLOB HEADERS "include/eosio/gps_plugin/*.hpp")
add_library( gps_plugin
             gps_plugin.cpp
             ${HEADERS} )

target_link_libraries( gps_plugin producer_plugin chain_plugin eosio_chain appbase )
target_include_directories( gps_plugin PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include" )
