file( GLOB HEADERS "include/eosio/jurisdiction_api_plugin/*.hpp" )
add_library( jurisdiction_api_plugin
             jurisdiction_api_plugin.cpp
             ${HEADERS} )

target_link_libraries( jurisdiction_api_plugin jurisdiction_plugin chain_plugin http_plugin appbase )
target_include_directories( jurisdiction_api_plugin PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include" )
