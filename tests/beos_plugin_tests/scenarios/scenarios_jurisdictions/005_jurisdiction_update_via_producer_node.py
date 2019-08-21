#!/usr/bin/python3
import os
import sys
import time
import datetime 
import requests
import json

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, init_cluster, ActionResult, ResourceResult, VotersResult

from beos_test_utils.beos_utils_pack import get_transaction_id_from_result

if __name__ == "__main__":
  try:
    number_of_pnodes  = 3
    producer_per_node = 1
    cluster, summary, args, log = init_cluster(__file__, number_of_pnodes, producer_per_node)
    cluster.run_all()

    code, mess = cluster.bios.make_cleos_call(["get", "info"])
    log.info("Bios: code: {0}, mess {1}\n".format(code, mess))
    for node in cluster.nodes:
      code, mess = node.make_cleos_call(["get", "info"])
      log.info("Nodes: code: {0}, mess {1}\n".format(code, mess))

    prods=[]
    for prod, data in cluster.producers.items(): 
      prods.append(prod)

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "1", "GERMANY", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info("{0}".format(result))

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "2", "RUSSIA", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info("{0}".format(result))

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "3", "CZECH REPUBLIC", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info("{0}".format(result))

    cluster.bios.wait_for_last_irreversible_block()

    idx = 0
    for node in cluster.nodes:
      call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[{1}]}} }}'.format(prods[idx], idx+1), "-p", "{0}".format(prods[idx])]
      code, result = node.make_cleos_call(call)
      log.info("{0}".format(result))
      idx += 1

    # log.info("Wait 60s for end of turn for each producer. We wait that long for jurisdiction change to take effect.")
    # time.sleep(60)
    cluster.wait_full_jurisdiction_cycle()

    log.info("Ask `get_producer_jurisdiction` for `{0}`".format(prods[0]))
    call = ["get", "producer_jurisdiction", '["{0}"]'.format(prods[0])]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(result)
    result = json.loads(result)
    summary.equal(True, len(result["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(result["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, result["producer_jurisdictions"][0]["jurisdictions"][0] == 1, "Expecting jurisdiction code 1" )

    log.info("Ask `get_producer_jurisdiction` for `{0}`".format(prods[1]))
    call = ["get", "producer_jurisdiction", '["{0}"]'.format(prods[1])]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(result)
    result = json.loads(result)
    summary.equal(True, len(result["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(result["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, result["producer_jurisdictions"][0]["jurisdictions"][0] == 2, "Expecting jurisdiction code 2" )

    log.info("Ask `get_producer_jurisdiction` for `{0}`".format(prods[2]))
    call = ["get", "producer_jurisdiction", '["{0}"]'.format(prods[2])]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(result)
    result = json.loads(result)
    summary.equal(True, len(result["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(result["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, result["producer_jurisdictions"][0]["jurisdictions"][0] == 3, "Expecting jurisdiction code 3" )

    call =[ "push", "action", "--jurisdictions", "[1]","beos.gateway", "issue", "[ \"{0}\", \"100.0000 BTS\", \"hello\" ]".format(prods[2]), "-p", "beos.gateway"]
    code, result = cluster.bios.make_cleos_call(call)
    trx_id = get_transaction_id_from_result(code, result)
    log.info("Waiting for transaction id: {} in block".format(trx_id))
    cluster.bios.wait_for_transaction_in_block(trx_id)

  except Exception as _ex:
    log.exception(_ex)
    summary.equal(False, True, "Exception occured durring testing.")
  finally:
    status = summary.summarize()
    cluster.stop_all()
    exit(status)