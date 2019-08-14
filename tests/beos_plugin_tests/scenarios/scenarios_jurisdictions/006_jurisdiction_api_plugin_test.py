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

    log.info("Adding test jurisdictions")
    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "1", "GERMANY", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    summary.equal(True, code == 0, "Expecting operation success")

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "2", "RUSSIA", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    summary.equal(True, code == 0, "Expecting operation success")

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "3", "CZECH REPUBLIC", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    summary.equal(True, code == 0, "Expecting operation success")

    log.info("Wait 10s. We will wait couple of blocks to be sure that jurisdiction data is added.")
    time.sleep(10)

    api_rpc_caller = cluster.bios.get_url_caller()

    log.info("Testing `get_all_jurisdictions` API call")
    ret = api_rpc_caller.jurisdiction.get_all_jurisdictions()
    summary.equal(True, len(ret["jurisdictions"]) == 3, "Expecting three jurisdictions")

    log.info("Testing `get_all_jurisdictions` API call with `limit 1`")
    data = {"limit" : 1}
    ret = api_rpc_caller.jurisdiction.get_all_jurisdictions(data)
    summary.equal(True, len(ret["jurisdictions"]) == 1, "Expecting one jurisdiction")

    log.info("Testing `get_all_jurisdictions` API call with `limit 1` and `last_code 2`")
    data = {"limit" : 1, "last_code" : 2}
    ret = api_rpc_caller.jurisdiction.get_all_jurisdictions(data)
    summary.equal(True, len(ret["jurisdictions"]) == 1, "Expecting one jurisdiction")
    summary.equal(True, ret["jurisdictions"][0]["code"] == 2, "Expecting code 2")

    log.info("Setting jurisdiction codes for producers")
    idx = 0
    for node in cluster.nodes:
      call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[{1}]}} }}'.format(prods[idx], idx+1), "-p", "{0}".format(prods[idx])]
      code, result = node.make_cleos_call(call)
      summary.equal(True, code == 0, "Expecting operation success")
      idx += 1

    log.info("Wait 60s for end of turn for each producer. We wait that long for jurisdiction change to take effect.")
    time.sleep(60)

    log.info("Testing `get_producer_jurisdiction` API call for `aaaaaaaaaaaa`")
    data = {"producer_names":["aaaaaaaaaaaa"]}
    ret = api_rpc_caller.jurisdiction.get_producer_jurisdiction(data)
    summary.equal(True, len(ret["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(ret["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, ret["producer_jurisdictions"][0]["jurisdictions"][0] == 1, "Expecting jurisdiction code 1" )

    log.info("Testing `get_producer_jurisdiction` API call for `baaaaaaaaaaa`")
    data = {"producer_names":["baaaaaaaaaaa"]}
    ret = api_rpc_caller.jurisdiction.get_producer_jurisdiction(data)
    summary.equal(True, len(ret["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(ret["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, ret["producer_jurisdictions"][0]["jurisdictions"][0] == 2, "Expecting jurisdiction code 2" )

    log.info("Testing `get_producer_jurisdiction` API call for `caaaaaaaaaaa`")
    data = {"producer_names":["caaaaaaaaaaa"]}
    ret = api_rpc_caller.jurisdiction.get_producer_jurisdiction(data)
    summary.equal(True, len(ret["producer_jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, len(ret["producer_jurisdictions"][0]["jurisdictions"]) == 1, "Expecting 1 element in array")
    summary.equal(True, ret["producer_jurisdictions"][0]["jurisdictions"][0] == 3, "Expecting jurisdiction code 3")

    log.info("Testing `get_producer_jurisdiction` API call for `aaaaaaaaaaaa`, `baaaaaaaaaaa` and `caaaaaaaaaaa`")
    data = {"producer_names":["aaaaaaaaaaaa","baaaaaaaaaaa","caaaaaaaaaaa"]}
    ret = api_rpc_caller.jurisdiction.get_producer_jurisdiction(data)
    summary.equal(True, len(ret["producer_jurisdictions"]) == 3, "Expecting 3 element in array")

    log.info("Testing `get_active_jurisdictions` API call")
    ret = api_rpc_caller.jurisdiction.get_active_jurisdictions()
    summary.equal(True, len(ret["jurisdictions"]) == 3, "Expecting 3 element in array")

    log.info("Testing `get_active_jurisdictions` API call with `limit 1`")
    data = {"limit" : 1}
    ret = api_rpc_caller.jurisdiction.get_active_jurisdictions(data)
    summary.equal(True, len(ret["jurisdictions"]) == 1, "Expecting 1 element in array")

  except Exception as _ex:
    log.exception(_ex)
    summary.equal(False, True, "Exception occured durring testing.")
  finally:
    status = summary.summarize()
    cluster.stop_all()
    exit(status)