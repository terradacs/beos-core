file(GLOB HEADERS "include/eosio/test_producer_plugin/*.hpp")
add_library( test_producer_plugin
             test_producer_plugin.cpp
             ${HEADERS} )

target_link_libraries( test_producer_plugin producer_plugin eosio_chain appbase )
target_include_directories( test_producer_plugin PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include" )
