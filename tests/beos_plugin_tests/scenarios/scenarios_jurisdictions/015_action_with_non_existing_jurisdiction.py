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

    ref_producers = ["aaaaaaaaaaaa","baaaaaaaaaaa","caaaaaaaaaaa"]

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

    call =[ "push", "action", "beos.gateway", "issue", "[ \"{0}\", \"100.0000 BTS\", \"hello\" ]".format(ref_producers[0]), "-p", "beos.gateway"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info("{0}".format(result))
    summary.equal(True, code == 0, "This call {0} should succeed".format(call) )    

    log.info("Wait 10s. We will wait couple of blocks to be sure that jurisdiction data is added.")
    time.sleep(10)

    api_rpc_caller = cluster.bios.get_url_caller()

    log.info("Wait for producer other than `aaaaaaaaaaaa`")
    # we will wait till active producer will be not aaaaaaaaaaaa
    ret = api_rpc_caller.chain.get_info()
    while ret["head_block_producer"] == ref_producers[0]:
      time.sleep(0.5)
      ret = api_rpc_caller.chain.get_info()

    call =["transfer", ref_producers[0], ref_producers[1], "100.0000 BTS", "hello", "--jurisdictions", "[4]"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info("{0}".format(result))
    result = json.loads(result)
    summary.equal(True, code == 0, "This call {0} should succeed".format(call) )
    summary.equal(True, result["status"] == "Transaction will be deferred due to the jurisdictions", "Transaction will be deferred due to the jurisdictions")

    log.info("Waiting for transaction {} to expire".format(result["trx_id"]))
    minutes_wait = 4
    for i in range(minutes_wait):
      log.info("Waiting... {} minutes to go...".format(minutes_wait - i))
      time.sleep(60)

    found = False
    with open(cluster.bios.log_file_path, 'r') as log_file:
      for line in log_file.readlines():
        if "expired transaction {}".format(result["trx_id"]) in line:
          found = True
          break

    summary.equal(True, found, "`expired transaction {}` found in logs".format(result["trx_id"]))

  except Exception as _ex:
    log.exception(_ex)
    summary.equal(False, True, "Exception occured durring testing: {}.".format(_ex))
  finally:
    status = summary.summarize()
    cluster.stop_all()
    exit(status)
