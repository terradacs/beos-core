
find_package( Gperftools QUIET )
if( GPERFTOOLS_FOUND )
    message( STATUS "Found gperftools; compiling tests with TCMalloc")
    list( APPEND PLATFORM_SPECIFIC_LIBS tcmalloc )
endif()

find_package(LLVM 4.0 REQUIRED CONFIG)

link_directories(${LLVM_LIBRARY_DIR})

set( CMAKE_CXX_STANDARD 14 )

include_directories("${CMAKE_SOURCE_DIR}/plugins/wallet_plugin/include")

file(GLOB UNIT_TESTS "*.cpp")

add_executable( plugin_test ${UNIT_TESTS} ${WASM_UNIT_TESTS} )
target_link_libraries( plugin_test eosio_testing eosio_chain chainbase eos_utilities chain_plugin wallet_plugin abi_generator fc ${PLATFORM_SPECIFIC_LIBS} )

target_include_directories( plugin_test PUBLIC
                            ${CMAKE_SOURCE_DIR}/plugins/net_plugin/include
                            ${CMAKE_SOURCE_DIR}/plugins/chain_plugin/include )
add_dependencies(plugin_test asserter test_api test_api_mem test_api_db test_api_multi_index proxy identity identity_test stltest infinite eosio.system eosio.token eosio.bios test.inline multi_index_test noop eosio.msig)

#
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/core_symbol.py.in ${CMAKE_CURRENT_BINARY_DIR}/core_symbol.py)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/testUtils.py ${CMAKE_CURRENT_BINARY_DIR}/testUtils.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/WalletMgr.py ${CMAKE_CURRENT_BINARY_DIR}/WalletMgr.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/Node.py ${CMAKE_CURRENT_BINARY_DIR}/Node.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/Cluster.py ${CMAKE_CURRENT_BINARY_DIR}/Cluster.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/TestHelper.py ${CMAKE_CURRENT_BINARY_DIR}/TestHelper.py COPYONLY)

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/p2p_tests/dawn_515/test.sh ${CMAKE_CURRENT_BINARY_DIR}/p2p_tests/dawn_515/test.sh COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/distributed-transactions-test.py ${CMAKE_CURRENT_BINARY_DIR}/distributed-transactions-test.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/distributed-transactions-remote-test.py ${CMAKE_CURRENT_BINARY_DIR}/distributed-transactions-remote-test.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/sample-cluster-map.json ${CMAKE_CURRENT_BINARY_DIR}/sample-cluster-map.json COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/restart-scenarios-test.py ${CMAKE_CURRENT_BINARY_DIR}/restart-scenarios-test.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/nodeos_forked_chain_test.py ${CMAKE_CURRENT_BINARY_DIR}/nodeos_forked_chain_test.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/nodeos_run_test.py ${CMAKE_CURRENT_BINARY_DIR}/nodeos_run_test.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/nodeos_run_remote_test.py ${CMAKE_CURRENT_BINARY_DIR}/nodeos_run_remote_test.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/nodeos_under_min_avail_ram.py ${CMAKE_CURRENT_BINARY_DIR}/nodeos_under_min_avail_ram.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/nodeos_voting_test.py ${CMAKE_CURRENT_BINARY_DIR}/nodeos_voting_test.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/consensus-validation-malicious-producers.py ${CMAKE_CURRENT_BINARY_DIR}/consensus-validation-malicious-producers.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/validate-dirty-db.py ${CMAKE_CURRENT_BINARY_DIR}/validate-dirty-db.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/launcher_test.py ${CMAKE_CURRENT_BINARY_DIR}/launcher_test.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/eos_voter_rpc_tests.py  ${CMAKE_CURRENT_BINARY_DIR}/eos_voter_rpc_tests.py  COPYONLY)

# copy beos test dirs to binary dir
execute_process(COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_SOURCE_DIR}/beos_plugin_tests ${CMAKE_CURRENT_BINARY_DIR}/beos_plugin_tests)
execute_process(COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_SOURCE_DIR}/beos_transfer_tests ${CMAKE_CURRENT_BINARY_DIR}/beos_transfer_tests)

#To run plugin_test with all log from blockchain displayed, put --verbose after --, i.e. plugin_test -- --verbose
add_test(NAME plugin_test COMMAND plugin_test --report_level=detailed --color_output)

add_test(NAME nodeos_sanity_test COMMAND tests/nodeos_run_test.py -v --sanity-test --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_property(TEST nodeos_sanity_test PROPERTY LABELS nonparallelizable_tests)
add_test(NAME nodeos_sanity_bnet_test COMMAND tests/nodeos_run_test.py -v --sanity-test --clean-run --p2p-plugin bnet --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_property(TEST nodeos_sanity_bnet_test PROPERTY LABELS nonparallelizable_tests)

# DISABLE_FAILING_TESTS was introduced to disable test with nondeteministic behaviour. Results of these test varies depending on
# machine properties.
if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME nodeos_run_test COMMAND tests/nodeos_run_test.py -v --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST nodeos_run_test PROPERTY LABELS nonparallelizable_tests)
else()
  message(WARNING "nodeos_run_test test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME nodeos_run_bnet_test COMMAND tests/nodeos_run_test.py -v --clean-run --p2p-plugin bnet --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST nodeos_run_bnet_test PROPERTY LABELS nonparallelizable_tests)
else()
  message(WARNING "nodeos_run_bnet_test test has been disabled")
endif()

add_test(NAME p2p_dawn515_test COMMAND tests/p2p_tests/dawn_515/test.sh WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_property(TEST p2p_dawn515_test PROPERTY LABELS nonparallelizable_tests)

if (NOT DISABLE_FAILING_TESTS)
  if(BUILD_MONGO_DB_PLUGIN)
    add_test(NAME nodeos_run_test-mongodb COMMAND tests/nodeos_run_test.py --mongodb -v --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
    set_property(TEST nodeos_run_test-mongodb PROPERTY LABELS nonparallelizable_tests)
  endif()
else()
  message(WARNING "nodeos_run_test-mongodb test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME distributed-transactions-test COMMAND tests/distributed-transactions-test.py -d 2 -p 4 -n 6 -v --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST distributed-transactions-test PROPERTY LABELS nonparallelizable_tests)
else()
  message(WARNING "distributed-transactions-test test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME distributed-transactions-bnet-test COMMAND tests/distributed-transactions-test.py -d 2 -p 1 -n 4 --p2p-plugin bnet -v --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST distributed-transactions-bnet-test PROPERTY LABELS nonparallelizable_tests)
else()
  message(WARNING "distributed-transactions-bnet-test test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME restart-scenarios-test-resync COMMAND tests/restart-scenarios-test.py -c resync -p4 -v --clean-run --dump-error-details WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST restart-scenarios-test-resync PROPERTY LABELS nonparallelizable_tests)
else()
  message(WARNING "restart-scenarios-test-resync test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME restart-scenarios-test-hard_replay COMMAND tests/restart-scenarios-test.py -c hardReplay -p4 -v --clean-run --dump-error-details WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST restart-scenarios-test-hard_replay PROPERTY LABELS nonparallelizable_tests)
else()
  message(WARNING "restart-scenarios-test-hard_replay test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME restart-scenarios-test-none COMMAND tests/restart-scenarios-test.py -c none --kill-sig term -p4 -v --clean-run --dump-error-details WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST restart-scenarios-test-none PROPERTY LABELS nonparallelizable_tests)
else()
  message(WARNING "restart-scenarios-test-none test has been disabled")
endif()

# TODO: add_test(NAME consensus-validation-malicious-producers COMMAND tests/consensus-validation-malicious-producers.py -w 80 --dump-error-details WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
add_test(NAME validate_dirty_db_test COMMAND tests/validate-dirty-db.py -v --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_property(TEST validate_dirty_db_test PROPERTY LABELS nonparallelizable_tests)

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME launcher_test COMMAND tests/launcher_test.py -v --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST launcher_test PROPERTY LABELS nonparallelizable_tests)
else()
  message(WARNING "launcher_test test has been disabled")
endif()

# Long running tests
add_test(NAME nodeos_sanity_lr_test COMMAND tests/nodeos_run_test.py -v --sanity-test --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_property(TEST nodeos_sanity_lr_test PROPERTY LABELS long_running_tests)
add_test(NAME nodeos_sanity_bnet_lr_test COMMAND tests/nodeos_run_test.py -v --sanity-test --p2p-plugin bnet --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_property(TEST nodeos_sanity_bnet_lr_test PROPERTY LABELS long_running_tests)

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME nodeos_run_check_lr_test COMMAND tests/nodeos_run_test.py -v --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST nodeos_run_check_lr_test PROPERTY LABELS long_running_tests)
else()
  message(WARNING "nodeos_run_check_lr_test test has been disabled")
endif()

#add_test(NAME distributed_transactions_lr_test COMMAND tests/distributed-transactions-test.py -d 2 -p 21 -n 21 -v --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
#set_property(TEST distributed_transactions_lr_test PROPERTY LABELS long_running_tests)

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME nodeos_forked_chain_lr_test COMMAND tests/nodeos_forked_chain_test.py -v --wallet-port 9901 --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST nodeos_forked_chain_lr_test PROPERTY LABELS long_running_tests)
else()
  message(WARNING "nodeos_forked_chain_lr_test test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME nodeos_voting_lr_test COMMAND tests/nodeos_voting_test.py -v --wallet-port 9902 --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST nodeos_voting_lr_test PROPERTY LABELS long_running_tests)
else()
  message(WARNING "nodeos_voting_lr_test test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME nodeos_voting_bnet_lr_test COMMAND tests/nodeos_voting_test.py -v --wallet-port 9903 --p2p-plugin bnet --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST nodeos_voting_bnet_lr_test PROPERTY LABELS long_running_tests)
else()
  message(WARNING "nodeos_voting_bnet_lr_test test has been disabled")
endif()

if (NOT DISABLE_FAILING_TESTS)
  add_test(NAME nodeos_under_min_avail_ram_lr_test COMMAND tests/nodeos_under_min_avail_ram.py -v --wallet-port 9904 --clean-run --dump-error-detail WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_property(TEST nodeos_under_min_avail_ram_lr_test PROPERTY LABELS long_running_tests)
else()
  message(WARNING "nodeos_under_min_avail_ram_lr_test test has been disabled")
endif()

add_test(NAME start_keosd_for_scenarios COMMAND run.py --wallet WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
add_test(NAME stop_keosd_for_scenarios COMMAND run.py --cancel --wallet WORKING_DIRECTORY ${CMAKE_BINARY_DIR})

add_test(NAME start_nodeos_keosd_via_run_py COMMAND run.py WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
add_test(NAME stop_nodeos_keosd_via_run_py COMMAND run.py --cancel WORKING_DIRECTORY ${CMAKE_BINARY_DIR})

set_property(TEST start_keosd_for_scenarios PROPERTY LABELS beos_tests)
set_tests_properties(stop_keosd_for_scenarios  PROPERTIES LABELS beos_tests DEPENDS start_keosd_for_scenarios)
set_property(TEST start_nodeos_keosd_via_run_py PROPERTY LABELS beos_tests)
set_tests_properties(stop_nodeos_keosd_via_run_py PROPERTIES LABELS beos_tests DEPENDS start_nodeos_keosd_via_run_py)

if(NOT DISABLE_FAILING_TESTS)
  set_tests_properties(start_keosd_for_scenarios PROPERTIES LABELS beos_tests DEPENDS nodeos_under_min_avail_ram_lr_test)
else()
  set_tests_properties(start_keosd_for_scenarios PROPERTIES LABELS beos_tests DEPENDS nodeos_sanity_bnet_lr_test)
endif()

set_property(TEST stop_keosd_for_scenarios APPEND PROPERTY DEPENDS start_keosd_for_scenarios)

macro(SUBDIRLIST result curdir)
  file(GLOB children RELATIVE ${curdir} ${curdir}/*)
  set(dirlist "")
  foreach(child ${children})
    if(IS_DIRECTORY ${curdir}/${child})
      list(APPEND dirlist ${child})
    endif()
  endforeach()
  set(${result} ${dirlist})
endmacro()

SUBDIRLIST(Scenarios ${CMAKE_BINARY_DIR}/tests/beos_plugin_tests/scenarios/)

list(LENGTH Scenarios nr_of_scenarios_folders)
math(EXPR nr_of_scenarios_folders "${nr_of_scenarios_folders}-1")
set(port_counter 1)
set(test_base_name "test03_scenarios_deploy_")
foreach(scenario_dir ${Scenarios})
  math(EXPR NODEOS_SCENARIO_PORT "10000+${port_counter}")
  set(test_name "${test_base_name}${scenario_dir}")
  add_test(NAME ${test_name} COMMAND tests/beos_plugin_tests/test03_scenarios_deploy.py
  --nodeos-ip ${NODEOS_IP_ADDRESS}
  --nodeos-port ${NODEOS_SCENARIO_PORT}
  --keosd-ip ${KEOSD_IP_ADDRESS}
  --keosd-port ${KEOSD_PORT} 
  --master-wallet-name ${MASTER_WALLET_NAME}
  --scenarios ${CMAKE_BINARY_DIR}/tests/beos_plugin_tests/scenarios/${scenario_dir}
  --path-to-cleos ${CMAKE_BINARY_DIR}/build/programs/cleos/
  --path-to-keosd ${CMAKE_BINARY_DIR}/build/programs/keosd/
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
  set_tests_properties( ${test_name} PROPERTIES LABELS beos_tests DEPENDS start_keosd_for_scenarios)
  set_property(TEST stop_keosd_for_scenarios APPEND PROPERTY DEPENDS ${test_name})
  set_property(TEST start_nodeos_keosd_via_run_py APPEND PROPERTY DEPENDS ${test_name})
  math(EXPR port_counter "${port_counter}+1")
endforeach()

set_property(TEST start_nodeos_keosd_via_run_py APPEND PROPERTY DEPENDS stop_keosd_for_scenarios )

add_test(NAME eos_voter_rpc_tests COMMAND python3 eos_voter_rpc_tests.py --nodeos-ip ${NODEOS_IP_ADDRESS} --nodeos-port ${NODEOS_PORT} WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/tests)
set_tests_properties(eos_voter_rpc_tests PROPERTIES LABELS beos_tests DEPENDS start_nodeos_keosd_via_run_py)

add_test(NAME test04_account_creation_and_get_account_deploy COMMAND tests/beos_plugin_tests/test04_account_creation_and_get_account_deploy.py --nodeos-ip ${NODEOS_IP_ADDRESS} --nodeos-port ${NODEOS_PORT}  --keosd-ip ${KEOSD_IP_ADDRESS}  --keosd-port ${KEOSD_PORT} --master-wallet-name ${MASTER_WALLET_NAME}  WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_tests_properties(test04_account_creation_and_get_account_deploy PROPERTIES LABELS beos_tests DEPENDS start_nodeos_keosd_via_run_py)

add_test(NAME test05_account_creation_with_delegate_ram COMMAND tests/beos_plugin_tests/test05_account_creation_with_delegate_ram.py  --main-dir ${CMAKE_BINARY_DIR} --nodeos-ip ${NODEOS_IP_ADDRESS} --nodeos-port ${NODEOS_PORT}  WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_tests_properties(test05_account_creation_with_delegate_ram PROPERTIES LABELS beos_tests DEPENDS start_nodeos_keosd_via_run_py)

add_test(NAME test06_account_creation_and_account_validator_deploy COMMAND tests/beos_plugin_tests/test06_account_creation_and_account_validator_deploy.py --nodeos-ip ${NODEOS_IP_ADDRESS} --nodeos-port ${NODEOS_PORT} --keosd-ip ${KEOSD_IP_ADDRESS}  --keosd-port ${KEOSD_PORT} --master-wallet-name ${MASTER_WALLET_NAME} WORKING_DIRECTORY ${CMAKE_BINARY_DIR} )
set_tests_properties(test06_account_creation_and_account_validator_deploy PROPERTIES LABELS beos_tests DEPENDS start_nodeos_keosd_via_run_py)

add_test(NAME test08_voting_test COMMAND tests/beos_plugin_tests/test08_voting_test.py  --main-dir ${CMAKE_BINARY_DIR} --nodeos-ip ${NODEOS_IP_ADDRESS} --nodeos-port ${NODEOS_PORT}  WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_tests_properties(test08_voting_test PROPERTIES LABELS beos_tests DEPENDS start_nodeos_keosd_via_run_py)

add_test(NAME test09_vote_actions_test COMMAND tests/beos_plugin_tests/test09_vote_actions_test.py  --main-dir ${CMAKE_BINARY_DIR} --nodeos-ip ${NODEOS_IP_ADDRESS} --nodeos-port ${NODEOS_PORT}  WORKING_DIRECTORY ${CMAKE_BINARY_DIR})
set_tests_properties(test09_vote_actions_test PROPERTIES LABELS beos_tests DEPENDS start_nodeos_keosd_via_run_py)


set_tests_properties(stop_nodeos_keosd_via_run_py PROPERTIES LABELS beos_tests DEPENDS start_nodeos_keosd_via_run_py)
set_property(TEST stop_nodeos_keosd_via_run_py APPEND PROPERTY DEPENDS test04_account_creation_and_get_account_deploy)
set_property(TEST stop_nodeos_keosd_via_run_py APPEND PROPERTY DEPENDS test05_account_creation_with_delegate_ram)
set_property(TEST stop_nodeos_keosd_via_run_py APPEND PROPERTY DEPENDS test06_account_creation_and_account_validator_deploy)
set_property(TEST stop_nodeos_keosd_via_run_py APPEND PROPERTY DEPENDS test08_voting_test)
set_property(TEST stop_nodeos_keosd_via_run_py APPEND PROPERTY DEPENDS test09_vote_actions_test)

if(ENABLE_COVERAGE_TESTING)

  set(Coverage_NAME ${PROJECT_NAME}_coverage)

  if(NOT LCOV_PATH)
    message(FATAL_ERROR "lcov not found! Aborting...")
  endif() # NOT LCOV_PATH

  if(NOT LLVMCOV_PATH)
    message(FATAL_ERROR "llvm-cov not found! Aborting...")
  endif() # NOT LCOV_PATH

  if(NOT GENHTML_PATH)
    message(FATAL_ERROR "genhtml not found! Aborting...")
  endif() # NOT GENHTML_PATH

  # no spaces allowed within tests list
  set(ctest_tests 'plugin_test|p2p_dawn515_test|nodeos_run_test|bnet_nodeos_run_test|distributed-transactions-test|restart-scenarios-test_resync')
  set(ctest_exclude_tests 'nodeos_run_remote_test|nodeos_run_test-mongodb|distributed-transactions-remote-test|restart-scenarios-test_replay')

  # Setup target
  add_custom_target(${Coverage_NAME}

    COMMAND ${LCOV_PATH} --directory . --zerocounters

    COMMAND ctest -R ${ctest_tests} -E ${ctest_exclude_tests}

    COMMENT "Capturing lcov counters and generating report"
    COMMAND ${LCOV_PATH} --directory . --capture --gcov-tool ${CMAKE_SOURCE_DIR}/tools/llvm-gcov.sh --output-file ${Coverage_NAME}.info

    COMMENT "Processing code coverage counters and generating report."
    COMMAND ${GENHTML_PATH} -o ${Coverage_NAME} ${PROJECT_BINARY_DIR}/${Coverage_NAME}.info
    COMMAND ${CMAKE_COMMAND} -E remove ${Coverage_NAME}.base ${Coverage_NAME}.info ${Coverage_NAME}.total ${PROJECT_BINARY_DIR}/${Coverage_NAME}.info.cleaned

    WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
    COMMENT "Resetting code coverage counters to zero. Processing code coverage counters and generating report."
    )

  # Show info where to find the report
  add_custom_command(TARGET ${Coverage_NAME} POST_BUILD
    COMMAND ;
    COMMENT "Open ./${Coverage_NAME}/index.html in your browser to view the coverage report."
    )
endif()
