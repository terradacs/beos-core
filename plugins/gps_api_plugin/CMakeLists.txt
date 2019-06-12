file( GLOB HEADERS "include/eosio/gps_api_plugin/*.hpp" )
add_library(   gps_api_plugin
               gps_api_plugin.cpp
               ${HEADERS} )

target_link_libraries( gps_api_plugin gps_plugin chain_plugin http_plugin appbase )
target_include_directories( gps_api_plugin PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include" )
