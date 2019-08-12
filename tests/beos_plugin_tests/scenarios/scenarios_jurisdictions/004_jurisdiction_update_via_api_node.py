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

from common import get_transaction_id_from_result

if __name__ == "__main__":
  try:
    number_of_pnodes  = 3
    producer_per_node = 1
    cluster, summary, args, log = init_cluster(__file__, number_of_pnodes, producer_per_node)
    cluster.run_all()

    log.info("Wait 5s")
    time.sleep(5)
    
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
    log.info(f"{result}")

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "2", "RUSSIA", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(f"{result}")

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "3", "CZECH REPUBLIC", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(f"{result}")

    log.info("Wait 5s. We will wait couple of blocks to be sure that jurisdiction data is added.")
    time.sleep(5)

    call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[1]}} }}'.format(prods[0]), "-p", f"{prods[0]}"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(f"{result}")

    call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[2]}} }}'.format(prods[1]), "-p", f"{prods[1]}"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(f"{result}")

    call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[3]}} }}'.format(prods[2]), "-p", f"{prods[2]}"]
    code, result = cluster.bios.make_cleos_call(call)
    log.info(f"{result}")

    log.info("Wait 60s for end of turn for each producer. We wait that long for jurisdiction change to take effect.")
    time.sleep(60)
    

    log.info("Ask `get_producer_jurisdiction` for `aaaaaaaaaaaa`")
    call = ["get", "producer_jurisdiction", '["aaaaaaaaaaaa"]']
    code, result = cluster.bios.make_cleos_call(call)
    log.info(result)
    result = json.loads(result)
    summary.equal(True, len(result["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(result["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, result["producer_jurisdictions"][0]["jurisdictions"][0] == 1, "Expecting jurisdiction code 1" )

    log.info("Ask `get_producer_jurisdiction` for `baaaaaaaaaaa`")
    call = ["get", "producer_jurisdiction", '["baaaaaaaaaaa"]']
    code, result = cluster.bios.make_cleos_call(call)
    log.info(result)
    result = json.loads(result)
    summary.equal(True, len(result["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(result["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, result["producer_jurisdictions"][0]["jurisdictions"][0] == 2, "Expecting jurisdiction code 2")

    log.info("Ask `get_producer_jurisdiction` for `caaaaaaaaaaa`")
    call = ["get", "producer_jurisdiction", '["caaaaaaaaaaa"]']
    code, result = cluster.bios.make_cleos_call(call)
    log.info(result)
    result = json.loads(result)
    summary.equal(True, len(result["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(result["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, result["producer_jurisdictions"][0]["jurisdictions"][0] == 3, "Expecting jurisdiction code 3")

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