#!/usr/bin/python3
import os
import sys
import time
import datetime 
import requests
import json
import threading

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, init_cluster, ActionResult, ResourceResult, VotersResult

from common import get_transaction_id_from_result
from common import set_jurisdiction_for_producer

if __name__ == "__main__":
  try:
    number_of_pnodes  = 3
    producer_per_node = 1
    cluster, summary, args, log = init_cluster(__file__, number_of_pnodes, producer_per_node)
    cluster.run_all()

    log.info("Wait 5s")
    time.sleep(5)

    log.info("Adding test jurisdictions")

    jurisdictions = [
      ["1", "GERMANY", "EAST EUROPE"],
      ["2", "RUSSIA", "EAST EUROPE"],
      ["3", "CZECH REPUBLIC", "EAST EUROPE"]
    ]

    for jurisdiction in jurisdictions:
      call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "{}", "{}", "{}" ]'.format(jurisdiction[0], jurisdiction[1], jurisdiction[2]), "-p", "eosio"]
      code, result = cluster.bios.make_cleos_call(call)
      summary.equal(True, code == 0, "Expecting operation success")

    log.info("Wait 10s. We will wait couple of blocks to be sure that jurisdiction data is added.")
    time.sleep(10)

    ref_producers = ["aaaaaaaaaaaa","baaaaaaaaaaa","caaaaaaaaaaa"]
    api_rpc_caller = cluster.bios.get_url_caller()

    ret = api_rpc_caller.chain.get_info()
    log.info(ret)
    from_date = ret["head_block_time"]

    # we will wait till active producer will be not aaaaaaaaaaaa
    while ret["head_block_producer"] == ref_producers[0]:
      time.sleep(0.5)
      ret = api_rpc_caller.chain.get_info()

    # now we will change jurisdiction code for non existing one
    set_jurisdiction_for_producer(cluster.nodes[0].get_url(), [4])
    time.sleep(10)

    # now we will add that jurisdiction so it will exists when the change will take effect
    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "4", "POLAND", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(result)

    time.sleep(60)

    ret = api_rpc_caller.chain.get_info()
    log.info(ret)
    to_date = ret["head_block_time"]

    log.info("Testing `get_all_producer_jurisdiction_for_block` API call")
    ret = api_rpc_caller.jurisdiction_history.get_all_producer_jurisdiction_for_block()
    log.info(ret)
    summary.equal(True, len(ret["producer_jurisdiction_for_block"]) == 1, "Expecting result len 1")
    summary.equal(True, ret["producer_jurisdiction_for_block"][0]["producer_name"] == ref_producers[0], "Expecting producer {}".format(ref_producers[0]))
    summary.equal(True, len(ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"]) == 1, "Expecting one jurisdiction code")
    summary.equal(True, ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"][0] == 4, "Expecting code {} got {}".format(4, ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"][0]))

  except Exception as _ex:
    log.exception(_ex)
    summary.equal(False, True, "Exception occured durring testing: {}.".format(_ex))
  finally:
    status = summary.summarize()
    cluster.stop_all()
    exit(status)
