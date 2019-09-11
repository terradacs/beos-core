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
from beos_test_utils.beos_utils_pack import init, start_cluster, ActionResult, ResourceResult, VotersResult

from common import get_transaction_id_from_result
from common import set_jurisdiction_for_producer

if __name__ == "__main__":
  try:
    number_of_pnodes  = 3
    producer_per_node = 1
    cluster, summary, args, log = start_cluster(__file__, number_of_pnodes, producer_per_node)
    #cluster.run_all()

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

    ref_producers = sorted(list(cluster.producers.keys()))
    api_rpc_caller = cluster.bios.get_url_caller()

    log.info("Wait for producer other than `{}`".format(ref_producers[0]))
    # we will wait till active producer will be not aaaaaaaaaaaa
    ret = api_rpc_caller.chain.get_info()
    while ret["head_block_producer"] == ref_producers[0]:
      time.sleep(0.5)
      ret = api_rpc_caller.chain.get_info()

    log.info("Change producer `{}` jurisdiction for not existing one ie: `4`".format(ref_producers[0]))
    # now we will change jurisdiction code for non existing one
    set_jurisdiction_for_producer(cluster.nodes[0].get_url(), [4])
    time.sleep(10)

    log.info("Waiting one minute for whole production cycle")
    time.sleep(60)

    log.info("Testing `get_all_producer_jurisdiction_for_block` API call")
    ret = api_rpc_caller.jurisdiction_history.get_all_producer_jurisdiction_for_block()
    log.info(ret)
    summary.equal(True, len(ret["producer_jurisdiction_for_block"]) == 0, "Expecting result len 0")

    found = False
    with open(cluster.nodes[0].log_file_path, 'r') as log_file:
      for line in log_file.readlines():
        if "jurisdiction doesn't exist" in line:
          found = True
          break

    summary.equal(True, found, "`jurisdiction doesn't exist` found in logs")
  except Exception as _ex:
    log.exception(_ex)
    summary.equal(False, True, "Exception occured durring testing: {}.".format(_ex))
  finally:
    status = summary.summarize()
    cluster.stop_all()
    exit(status)
