#!/usr/bin/python3

import os
import sys
import time
import datetime
import requests
import json

if os.path.exists(os.path.dirname(os.path.abspath(__file__))+ "/logs/"+ __file__):
    exit(0)

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, start_cluster, ActionResult, ResourceResult, VotersResult

def generate_jur_array( amount : int = 100 , begin_with : int = 1):
	template_string = '{\"new_code\":nc,\"new_name\":\"nn\",\"new_description\":\"desc\"}dd'
	return_data = ""
	for i in range(begin_with, begin_with + amount):
		return_data += template_string.replace("nc", str(i)).replace("nn", "name{}".format(i)).replace("dd", "," if i != (begin_with + amount) - 1 else "" )
	
	return "[{}]".format(return_data)


number_of_pnodes = 3
producer_per_node = 1

if __name__ == "__main__":
	
	cluster, summary, args, log = start_cluster(
		__file__, number_of_pnodes, producer_per_node)
	
	try:
		# cluster.run_all()

		#Setting up
		code, mess = cluster.bios.make_cleos_call( ["get", "info"] )
		log.info("Bios: code: {0}, mess {1}\n".format(code, mess))

		for node in cluster.nodes:
			code, mess = cluster.bios.make_cleos_call(["get", "info"])
			log.info("Nodes: code: {0}, mess {1}\n".format(code, mess))

		prods = []
		for prod, data in cluster.producers.items():
			prods.append(prod)

		rpc = cluster.nodes[0].get_url_caller()
		response = rpc.chain.get_table_rows({"scope":"eosio", "code":"eosio", "table":"infojurisdic", "json": True})
		summary.equal(len(response["rows"]), 0, "There should be 0 jurisdictions.")

		log.info(cluster.bios.make_cleos_call(["push", "action", "eosio", "addmultijurs", '{\"new_jurisdicts\": data}'.replace("data", generate_jur_array(100)), "-p", "eosio"]))
		_, resSTR = cluster.bios.make_cleos_call(["get", "all_jurisdictions"])
		summary.equal(100, len(json.loads(resSTR)["jurisdictions"]))

		log.info(cluster.bios.make_cleos_call(["push", "action", "eosio", "addmultijurs", '{\"new_jurisdicts\": data}'.replace("data", generate_jur_array(100, 101)), "-p", "eosio"]))
		_, resSTR = cluster.bios.make_cleos_call(["get", "all_jurisdictions"])
		summary.equal(200, len(json.loads(resSTR)["jurisdictions"]))
		log.info(response)
		
	except Exception as _ex:
		log.exception(_ex)
	finally:
		summary_status = summary.summarize()
		cluster.stop_all()
		exit(summary_status)