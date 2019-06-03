file(GLOB HEADERS "include/eosio/jurisdiction_history_plugin/*.hpp" )
add_library( jurisdiction_history_plugin
             jurisdiction_history_plugin.cpp
             ${HEADERS} )

target_link_libraries( jurisdiction_history_plugin chain_plugin appbase fc )
target_include_directories( jurisdiction_history_plugin PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include ${CMAKE_CURRENT_SOURCE_DIR}/../chain_interface/include  "${CMAKE_CURRENT_SOURCE_DIR}/../../libraries/appbase/include")
