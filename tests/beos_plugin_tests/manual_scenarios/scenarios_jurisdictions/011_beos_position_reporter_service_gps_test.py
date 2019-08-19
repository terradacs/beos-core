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
from beos_test_utils.beos_utils_pack import init, init_cluster, ActionResult, ResourceResult, VotersResult

from common import get_transaction_id_from_result

if __name__ == "__main__":
  fake_gps = None
  reporter = None
  try:
    number_of_pnodes  = 3
    producer_per_node = 1
    cluster, summary, args, log = init_cluster(__file__, number_of_pnodes, producer_per_node)
    cluster.run_all()

    log.info("Wait 5s")
    time.sleep(5)

    log.info("Adding test jurisdictions")

    jurisdictions = [
      ["1", "Poland", "EAST EUROPE"],
      ["2", "Czechia", "EAST EUROPE"],
      ["3", "Germany", "EAST EUROPE"],
      ["4", "Netherlands", "WEST EUROPE"],
#      ["5", "Belgium", "WEST EUROPE"],
      ["6", "France", "WEST EUROPE"],
      ["7", "Austria", "WEST EUROPE"],
      ["8", "Slovakia", "EAST EUROPE"],
      ["9", "Ukraine", "EAST EUROPE"],
    ]

    for jurisdiction in jurisdictions:
      call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "{}", "{}", "{}" ]'.format(jurisdiction[0], jurisdiction[1], jurisdiction[2]), "-p", "eosio"]
      code, result = cluster.bios.make_cleos_call(call)
      summary.equal(True, code == 0, "Expecting operation success")

    log.info("Wait 10s. We will wait couple of blocks to be sure that jurisdiction data is added.")
    time.sleep(10)

    ref_jurisdictions = [1,2,3,4,6,7,8,9]
    ref_producers = ["aaaaaaaaaaaa","baaaaaaaaaaa","caaaaaaaaaaa"]

    log.info("Starting gpsfake")
    # -c is delay between sentences, since there are three sentences per one point
    # and default reporting interval is 60s the delay is set to 20s
    fake_gps = subprocess.Popen(["gpsfake","-q","-c",str(20.),"./test_data.nmea"])
    log.info(fake_gps.args)
    log.info(fake_gps.returncode)
    time.sleep(0.1)

    parameters = [args.position_reporter_path + "/jurisdiction_reporter.py"]
    parameters += ["--api-node-url", cluster.bios.get_url()]
    parameters += ["--producer-node-url", cluster.nodes[0].get_url()]
    parameters += ["--map-dir", args.position_reporter_path]
    parameters += ["poller", "gps"]
    parameters += ["--max-fix-age", "600000000"]
    log.info(parameters)

    reporter = subprocess.Popen(parameters)
    log.info(reporter.returncode)

    api_rpc_caller = cluster.bios.get_url_caller()

    ret = api_rpc_caller.chain.get_info()
    #log.info(ret)
    from_date = ret["head_block_time"]

    log.info("Wait for initial fix - 60 seconds")
    time.sleep(60)

    jurisdictions_count = len(jurisdictions)
    log.info("Wait {} minutes for code changer to change codes for producer {}.".format(jurisdictions_count + 1, ref_producers[0]))
    for i in range(jurisdictions_count + 1):
      log.info("{} minutes to go".format(jurisdictions_count + 1 - i))
      time.sleep(60)
    
    ret = api_rpc_caller.chain.get_info()
    #log.info(ret)
    to_date = ret["head_block_time"]

    log.info("Testing `get_all_producer_jurisdiction_for_block` API call")
    ret = api_rpc_caller.jurisdiction_history.get_all_producer_jurisdiction_for_block()
    log.info(ret)
    summary.equal(True, len(ret["producer_jurisdiction_for_block"]) == 1, "Expecting result len 1")
    summary.equal(True, ret["producer_jurisdiction_for_block"][0]["producer_name"] == ref_producers[0], "Expecting producer {}".format(ref_producers[0]))
    summary.equal(True, len(ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"]) == 1, "Expecting one jurisdiction code")
    summary.equal(True, ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"][0] == ref_jurisdictions[-1], "Expecting code {} got {}".format(ref_jurisdictions[-1], ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"][0]))

    data = {
      "producer" : ref_producers[0],
      "from_date" : from_date,
      "to_date" : to_date,
      "limit" : 1000
    }
    log.info("Testing `get_producer_jurisdiction_history` API call with {}".format(data))
    ret = api_rpc_caller.jurisdiction_history.get_producer_jurisdiction_history(data)
    summary.equal(True, len(ret["producer_jurisdiction_history"]) == len(ref_jurisdictions), "Expecing result len {}".format(len(ref_jurisdictions)))
    for idx in range(len(ref_jurisdictions)):
      summary.equal(True, ret["producer_jurisdiction_history"][idx]["producer_name"] == ref_producers[0], "Expecting producer name {}".format(ref_producers[0]))
      summary.equal(True, ret["producer_jurisdiction_history"][idx]["new_jurisdictions"][0] == ref_jurisdictions[idx], "Expecting code {} got {}".format(ref_jurisdictions[idx], ret["producer_jurisdiction_history"][idx]["new_jurisdictions"][0]))

  except Exception as _ex:
    log.exception(_ex)
    summary.equal(False, True, "Exception occured durring testing.")
  finally:
    status = summary.summarize()
    cluster.stop_all()
    if reporter is not None:
      reporter.terminate()
    if fake_gps is not None:
      fake_gps.terminate()
    exit(status)
