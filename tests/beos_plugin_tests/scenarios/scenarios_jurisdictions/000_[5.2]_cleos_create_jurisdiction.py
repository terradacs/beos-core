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

    return_str = "{\"ram_payer\":\"eosio\",\"new_code\":0,\"new_name\":\"POLAND\",\"new_description\":\"EAST EUROPE\"}"

    call = ["push", "action", "eosio", "addjurisdict", "[ \"eosio\", \"0\", \"POLAND\", \"EAST EUROPE\" ]", "-p", "eosio"]
    result = node.make_cleos_call(call)
    log.info(result)
    summary.equal(True, result.find(return_str) != -1, "Expected: {}".format(return_str))

    node.wait_n_blocks(10)

    # trying to create jurisdiction with code equal to existing code
    call = ["push", "action", "eosio", "addjurisdict", "[ \"eosio\", \"0\", \"POLAND\", \"EAST EUROPE\" ]", "-p", "eosio"]
    result = node.make_cleos_call(call)
    print("result {}".format(result))
    log.info(result)
    summary.equal(True, result.find("jurisdiction with the same code exists") != -1, "jurisdiction with the same code exists")

    # trying to create jurisdiction with empty code
    call = ["push", "action", "eosio", "addjurisdict", "[ \"eosio\", \"\", \"POLAND\", \"EAST EUROPE\" ]", "-p", "eosio"]
    result = node.make_cleos_call(call)
    print("result {}".format(result))
    log.info(result)
    summary.equal(True, result.find("Couldn't parse uint64_t") != -1, "Couldn't parse uint64_t")

    # trying to create jurisdiction with existing name
    call = ["push", "action", "eosio", "addjurisdict", "[ \"eosio\", \"1\", \"POLAND\", \"EAST EUROPE\" ]", "-p", "eosio"]
    result = node.make_cleos_call(call)
    print("result {}".format(result))
    log.info(result)
    summary.equal(True, result.find("jurisdiction with the same name exists") != -1, "jurisdiction with the same name exists")

    # trying to create jurisdiction with negative code
    call = ["push", "action", "eosio", "addjurisdict", "[ \"eosio\", \"-1\", \"NEGATIVE\", \"EAST EUROPE\" ]", "-p", "eosio"]
    result = node.make_cleos_call(call)
    print("result {}".format(result))
    log.info(result)
    summary.equal(True, result.find("jurisdiction with the same name exists") != -1, "jurisdiction with the same name exists")

    # trying to create jurisdiction with empty description
    return_str = "{\"ram_payer\":\"eosio\",\"new_code\":2,\"new_name\":\"GERMANY\",\"new_description\":\"\"}"

    call = ["push", "action", "eosio", "addjurisdict", "[ \"eosio\", \"2\", \"GERMANY\", \"\" ]", "-p", "eosio"]
    result = node.make_cleos_call(call)
    log.info(result)
    summary.equal(True, result.find(return_str) != -1, "Expected: {}".format(return_str))

    node.wait_n_blocks(10)


  except Exception as _ex:
    log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
    summary.equal(False, True, "Exception occured durring testing.")
  finally:
    summary_status = summary.summarize()
    node.stop_node()
    exit(summary_status)
