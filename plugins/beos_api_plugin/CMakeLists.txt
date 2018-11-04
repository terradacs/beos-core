file( GLOB HEADERS "include/eosio/beos_api_plugin/*.hpp" )
add_library( beos_api_plugin
             beos_api_plugin.cpp
             ${HEADERS} )

target_link_libraries( beos_api_plugin beos_plugin chain_plugin http_plugin appbase )
target_include_directories( beos_api_plugin PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include" )
