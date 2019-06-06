#!/usr/bin/python3

import os
import sys
import time
import datetime 

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
  try:
    node, summary, args, log = init(__file__)
    node.run_node()

    return_str = '{"ram_payer":"eosio","new_code":0,"new_name":"POLAND","new_description":"EAST EUROPE"}'

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "0", "POLAND", "EAST EUROPE" ]', "-p", "eosio"]
    result = node.make_cleos_call(call)
    log.info(result)
    summary.equal(True, result.find(return_str) != -1, "Expected: {}".format(return_str))

    node.wait_n_blocks(5)

    return_str = '{"ram_payer":"eosio","new_code":1,"new_name":"GERMANY","new_description":"EAST EUROPE"}'

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "1", "GERMANY", "EAST EUROPE" ]', "-p", "eosio"]
    result = node.make_cleos_call(call)
    log.info(result)
    summary.equal(True, result.find(return_str) != -1, "Expected: {}".format(return_str))

    node.wait_n_blocks(5)

    return_str = '{"ram_payer":"eosio","new_code":2,"new_name":"RUSSIA","new_description":"EAST EUROPE"}'

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "2", "RUSSIA", "EAST EUROPE" ]', "-p", "eosio"]
    result = node.make_cleos_call(call)
    log.info(result)
    summary.equal(True, result.find(return_str) != -1, "Expected: {}".format(return_str))

    node.wait_n_blocks(5)

    return_str = '{"producer":"eosio","jurisdictions":[1]}'

    call = ["push", "action", "eosio", "updateprod", '{"data":{"producer":"eosio", "jurisdictions":[1]} }', "-p", "eosio"]
    result = node.make_cleos_call(call)
    log.info(result)
    summary.equal(True, result.find(return_str) != -1, "Expected: {}".format(return_str))

    node.wait_n_blocks(5)

    return_str = '{"producer":"eosio","jurisdictions":[1,2]}'

    call = ["push", "action", "eosio", "updateprod", '{"data":{"producer":"eosio", "jurisdictions":[1,2]} }', "-p", "eosio"]
    result = node.make_cleos_call(call)
    log.info(result)
    summary.equal(True, result.find(return_str) != -1, "Expected: {}".format(return_str))

    node.wait_n_blocks(5)

    call = ["push", "action", "eosio", "updateprod", '{"data":{"producer":"eosio", "jurisdictions":[3]} }', "-p", "eosio"]
    result = node.make_cleos_call(call)
    log.info(result)
    summary.equal(True, result.find("jurisdiction doesn't exist") != -1, "Expected: {}".format("jurisdiction doesn't exist"))

    node.wait_n_blocks(5)

  except Exception as _ex:
    log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
    summary.equal(False, True, "Exception occured durring testing.")
  finally:
    summary_status = summary.summarize()
    node.stop_node()
    exit(summary_status)
