file(GLOB HEADERS "include/eosio/beos_plugin/*.hpp")
add_library( beos_plugin
             beos_plugin.cpp
             ${HEADERS} )

target_link_libraries( beos_plugin chain_plugin eosio_chain appbase )
target_include_directories( beos_plugin PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include" )
