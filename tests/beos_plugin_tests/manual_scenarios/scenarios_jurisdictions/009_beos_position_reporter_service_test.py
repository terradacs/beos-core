#!/usr/bin/python3
import os
import sys
import time
import datetime 
import requests
import json
import subprocess

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, start_cluster, ActionResult, ResourceResult, VotersResult

from common import get_transaction_id_from_result

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
      ["3", "CZECH REPUBLIC", "EAST EUROPE"],
      ["4", "IRELAND", "WEST EUROPE"],
      ["5", "SPAIN", "WEST EUROPE"],
      ["6", "FRANCE", "WEST EUROPE"],
      ["7", "UKRAINE", "EAST EUROPE"],
      ["8", "POLAND", "EAST EUROPE"],
      ["9", "SLOVAKIA", "EAST EUROPE"]
    ]

    for jurisdiction in jurisdictions:
      call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "{}", "{}", "{}" ]'.format(jurisdiction[0], jurisdiction[1], jurisdiction[2]), "-p", "eosio"]
      code, result = cluster.bios.make_cleos_call(call)
      summary.equal(True, code == 0, "Expecting operation success")

    log.info("Wait 10s. We will wait couple of blocks to be sure that jurisdiction data is added.")
    time.sleep(10)

    ref_jurisdictions = [[1,2,3],[4,5,6],[7,8,9]]
    ref_producers = ["aaaaaaaaaaaa","baaaaaaaaaaa","caaaaaaaaaaa"]

    idx = 0
    reporters = []
    for node in cluster.nodes:
      parameters = [args.position_reporter_path, "--api-node-url", cluster.bios.get_url(), "--producer-node-url", node.get_url(), "code"]
      parameters += [str(x) for x in ref_jurisdictions[idx]]
      parameters += ["--code-in-sequence"]
      log.info(parameters)
      reporters.append(subprocess.Popen(parameters))
      idx += 1

    api_rpc_caller = cluster.bios.get_url_caller()

    ret = api_rpc_caller.chain.get_info()
    #log.info(ret)
    from_date = ret["head_block_time"]

    log.info("Wait 3 minutes for code changers to change codes for all producers.")
    time.sleep(3 * 60)
    
    ret = api_rpc_caller.chain.get_info()
    #log.info(ret)
    to_date = ret["head_block_time"]

    log.info("Testing `get_all_producer_jurisdiction_for_block` API call")
    ret = api_rpc_caller.jurisdiction_history.get_all_producer_jurisdiction_for_block()
    log.info(ret)
    summary.equal(True, len(ret["producer_jurisdiction_for_block"]) == 3, "Expecting result len 3")
    for idx in range(3):
      summary.equal(True, ret["producer_jurisdiction_for_block"][idx]["producer_name"] == ref_producers[idx], "Expecting producer {}".format(ref_producers[idx]))
      summary.equal(True, len(ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"]) == 1, "Expecting one jurisdiction code")
      summary.equal(True, ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"][0] == ref_jurisdictions[idx][2], "Expecting code {} got {}".format(ref_jurisdictions[idx][2], ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"][0]))

    ref_jurisdictions_idx = 0
    for producer in ref_producers:
      data = {
        "producer" : producer,
        "from_date" : from_date,
        "to_date" : to_date,
        "limit" : 1000
      }
      log.info("Testing `get_producer_jurisdiction_history` API call with {}".format(data))
      ret = api_rpc_caller.jurisdiction_history.get_producer_jurisdiction_history(data)
      log.info(ret)
      summary.equal(True, len(ret["producer_jurisdiction_history"]) == 3, "Expecing result len 3")
      for idx in range(3):
        summary.equal(True, ret["producer_jurisdiction_history"][idx]["producer_name"] == producer, "Expecting producer name {}".format(producer))
        summary.equal(True, ret["producer_jurisdiction_history"][idx]["new_jurisdictions"][0] == ref_jurisdictions[ref_jurisdictions_idx][idx], "Expecting code {} got {}".format(ref_jurisdictions[ref_jurisdictions_idx][idx], ret["producer_jurisdiction_history"][idx]["new_jurisdictions"][0]))
      ref_jurisdictions_idx += 1

  except Exception as _ex:
    log.exception(_ex)
    summary.equal(False, True, "Exception occured durring testing.")
  finally:
    status = summary.summarize()
    cluster.stop_all()
    for reporter in reporters:
      reporter.kill()
    exit(status)
