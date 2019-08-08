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
    assert code == 0, "Expecting operation success"

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "2", "RUSSIA", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    assert code == 0, "Expecting operation success"

    call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "3", "CZECH REPUBLIC", "EAST EUROPE" ]', "-p", "eosio"]
    code, result = cluster.bios.make_cleos_call(call)
    assert code == 0, "Expecting operation success"

    log.info("Wait 10s. We will wait couple of blocks to be sure that jurisdiction data is added.")
    time.sleep(10)

    api_rpc_caller = cluster.bios.get_url_caller()

    ret = api_rpc_caller.chain.get_info()
    #log.info(ret)
    from_date = ret["head_block_time"]
    block_number_begin = ret["head_block_num"]

    log.info("Setting initial jurisdiction codes for producers")
    idx = 0
    jurisdictions = [1,2,3]
    for node in cluster.nodes:
      call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[{1}]}} }}'.format(prods[idx], jurisdictions[idx]), "-p", f"{prods[idx]}"]
      code, result = node.make_cleos_call(call)
      assert code == 0, "Expecting operation success"
      idx += 1

    log.info("Wait 60s for end of turn for each producer. We wait that long for jurisdiction change to take effect.")
    time.sleep(60)

    ret = api_rpc_caller.chain.get_info()
    #log.info(ret)
    block_number_first_change = ret["head_block_num"]

    log.info("Changing initial jurisdictions for producers")
    idx = 0
    jurisdictions = [2,3,1]
    for node in cluster.nodes:
      call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[{1}]}} }}'.format(prods[idx], jurisdictions[idx]), "-p", f"{prods[idx]}"]
      code, result = node.make_cleos_call(call)
      assert code == 0, "Expecting operation success"
      idx += 1

    log.info("Wait 60s for end of turn for each producer. We wait that long for jurisdiction change to take effect.")
    time.sleep(60)

    ret = api_rpc_caller.chain.get_info()
    #log.info(ret)
    block_number_second_change = ret["head_block_num"]

    log.info("Changing jurisdictions for producers")
    idx = 0
    jurisdictions = [3,1,2]
    for node in cluster.nodes:
      call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[{1}]}} }}'.format(prods[idx], jurisdictions[idx]), "-p", f"{prods[idx]}"]
      code, result = node.make_cleos_call(call)
      assert code == 0, "Expecting operation success"
      idx += 1

    log.info("Wait 60s for end of turn for each producer. We wait that long for jurisdiction change to take effect.")
    time.sleep(60)

    ret = api_rpc_caller.chain.get_info()
    #log.info(ret)
    to_date = ret["head_block_time"]
    block_number_third_change = ret["head_block_num"]

    ref_jurisdictions = [[1,2,3],[2,3,1],[3,1,2]]
    ref_producers = ["aaaaaaaaaaaa","baaaaaaaaaaa","caaaaaaaaaaa"]

    log.info("Testing `get_all_producer_jurisdiction_for_block` API call")
    ret = api_rpc_caller.jurisdiction_history.get_all_producer_jurisdiction_for_block()
    #log.info(ret)
    assert len(ret["producer_jurisdiction_for_block"]) == 3, "Expecting result len 3"
    for idx in range(3):
      assert ret["producer_jurisdiction_for_block"][idx]["producer_name"] == ref_producers[idx], "Expecting producer {}".format(ref_producers[idx])
      assert len(ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"]) == 1, "Expecting one jurisdiction code"
      assert ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"][0] == ref_jurisdictions[idx][2], "Expecting code {} got {}".format(ref_jurisdictions[idx][2], ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"][0])

    log.info("Testing `get_all_producer_jurisdiction_for_block` API call with `block_number {}`".format(block_number_begin))
    data = {"block_number" : block_number_begin}
    ret = api_rpc_caller.jurisdiction_history.get_all_producer_jurisdiction_for_block(data)
    #log.info(ret)
    assert len(ret["producer_jurisdiction_for_block"]) == 0, "Expecting no result"

    ref_jurisdictions_idx = 0
    for block_number in [block_number_first_change, block_number_second_change, block_number_third_change]:
      log.info("Testing `get_all_producer_jurisdiction_for_block` API call with `block_number {}`".format(block_number))
      data = {"block_number" : block_number}
      ret = api_rpc_caller.jurisdiction_history.get_all_producer_jurisdiction_for_block(data)
      #log.info(ret)
      assert len(ret["producer_jurisdiction_for_block"]) == 3, "Expecting result len 3"
      for idx in range(3):
        assert ret["producer_jurisdiction_for_block"][idx]["producer_name"] == ref_producers[idx], "Expecting producer {}".format(ref_producers[idx])
        assert len(ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"]) == 1, "Expecting one jurisdiction code"
        assert ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"][0] == ref_jurisdictions[idx][ref_jurisdictions_idx], "Expecting code {} got {}".format(ref_jurisdictions[idx][ref_jurisdictions_idx], ret["producer_jurisdiction_for_block"][idx]["new_jurisdictions"][0])
      ref_jurisdictions_idx += 1

    for producer in ref_producers:
      log.info("Testing `get_producer_jurisdiction_for_block` API call with `block_number {}` and `producer {}`".format(block_number_begin, producer))
      data = {"block_number" : block_number_begin, "producer" : producer}
      ret = api_rpc_caller.jurisdiction_history.get_producer_jurisdiction_for_block(data)
      #log.info(ret)
      assert len(ret["producer_jurisdiction_for_block"]) == 0, "Expecting no result"

    ref_jurisdictions_idx = 0
    for block_number in [block_number_first_change, block_number_second_change, block_number_third_change]:
      for idx in range(3):
        log.info("Testing `get_producer_jurisdiction_for_block` API call with `block_number {}` and `producer {}`".format(block_number, ref_producers[idx]))
        data = {"block_number" : block_number, "producer" : ref_producers[idx]}
        ret = api_rpc_caller.jurisdiction_history.get_producer_jurisdiction_for_block(data)
        #log.info(ret)
        assert len(ret["producer_jurisdiction_for_block"]) == 1, "Expecting one result"
        assert ret["producer_jurisdiction_for_block"][0]["producer_name"] == ref_producers[idx], "Expecting producer {}".format(ref_producers[idx])
        assert len(ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"]) == 1, "Expecting one jurisdiction code"
        assert ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"][0] == ref_jurisdictions[idx][ref_jurisdictions_idx], "Expecting code {} got {}".format(ref_jurisdictions[idx][ref_jurisdictions_idx], ret["producer_jurisdiction_for_block"][0]["new_jurisdictions"][0])
      ref_jurisdictions_idx += 1

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
      #log.info(ret)
      assert len(ret["producer_jurisdiction_history"]) == 3, "Expecing result len 3"
      for idx in range(3):
        assert ret["producer_jurisdiction_history"][idx]["producer_name"] == producer, "Expecting producer name {}".format(producer)
        assert ret["producer_jurisdiction_history"][idx]["new_jurisdictions"][0] == ref_jurisdictions[ref_jurisdictions_idx][idx], "Expecting code {} got {}".format(ref_jurisdictions[ref_jurisdictions_idx][idx], ret["producer_jurisdiction_history"][idx]["new_jurisdictions"][0])
      ref_jurisdictions_idx += 1

  except Exception as _ex:
    log.exception(_ex)
  finally:
    cluster.stop_all()
    exit(0)