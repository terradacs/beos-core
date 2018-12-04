file( GLOB HEADERS "include/eosio/test_producer_api_plugin/*.hpp" )
add_library( test_producer_api_plugin
             test_producer_api_plugin.cpp
             ${HEADERS} )

target_link_libraries( test_producer_api_plugin test_producer_plugin chain_plugin http_plugin appbase )
target_include_directories( test_producer_api_plugin PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include" )
