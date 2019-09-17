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
		number_of_pnodes	= 2
		producer_per_node = 3
		cluster, summary, args, log = start_cluster(__file__, number_of_pnodes, producer_per_node)
		#cluster.run_all()

		log.info("Wait 5s")
		time.sleep(5)
		ref_producers = sorted(list(cluster.producers.keys()))

		log.info("Adding test jurisdictions")

		#Minimum is: (amount of nodes) * (amount of producers per node) + 1
		jurisdictions_tests = [
			["1", "GERMANY", "EAST EUROPE"],
			# ["2", "RUSSIA", "EAST EUROPE"],
			# ["3", "CZECH REPUBLIC", "EAST EUROPE"],
			["2", "POLAND", "EAST EUROPE"]
		]

		jurisdictions = list()
		
		for i in range(len(jurisdictions_tests) + 1, len(jurisdictions_tests) + 2 + len(cluster.producers) ):
			jurisdictions.append([ "{}".format(i), "jur{}".format(i), "sample_desc" ])

		for jurisdiction in jurisdictions:
			call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "{}", "{}", "{}" ]'.format(jurisdiction[0], jurisdiction[1], jurisdiction[2]), "-p", "eosio"]
			code, result = cluster.bios.make_cleos_call(call)
			summary.equal(True, code == 0, "Expecting operation success")

		for jurisdiction in jurisdictions_tests:
			call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "{}", "{}", "{}" ]'.format(jurisdiction[0], jurisdiction[1], jurisdiction[2]), "-p", "eosio"]
			code, result = cluster.bios.make_cleos_call(call)
			summary.equal(True, code == 0, "Expecting operation success")

		log.info("Wait 10s. We will wait couple of blocks to be sure that jurisdiction data is added.")
		time.sleep(10)

		jur_idx = 0
		for prod in ref_producers:
			resINT, resSTR = cluster.bios.make_cleos_call([
					"push", "action", "eosio" ,"updateprod", 
					'{"data":{ "producer":"' + str(prod) + 
					'", "jurisdictions":[' + str(jurisdictions[jur_idx][0]) + '] }}', "-p", prod ])
			jur_idx += 1

		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio.token", "issue",
		'["{}", "100000.0000 BTS", "for ice-creams"]'.format(ref_producers[0]), "-p", "beos.gateway"])
		summary.equal(0, resINT)
		if resINT:
			log.info(resSTR)
		
		api_rpc_caller = cluster.bios.get_url_caller()
		log.info("Wait for producer other than `{}`".format(ref_producers[0]))
		cluster.bios.wait_for_last_irreversible_block()

		# we will wait till active producer will be not aaaaaaaaaaaa
		ret = api_rpc_caller.chain.get_info()
		while ret["head_block_producer"] == ref_producers[0]:
			time.sleep(0.5)
			ret = api_rpc_caller.chain.get_info()

		jur_idx = len(jurisdictions_tests) + 1
		#updateprod burst loop
		for jur in jurisdictions_tests:
			log.info("Change producer `{}` jurisdiction for existing one ie: `{}`".format(ref_producers[0], jur))
			resINT, resSTR = cluster.nodes[0].make_cleos_call(["push", "action",
			"-u", "[{}]".format(jur_idx), "eosio", "updateprod", 
			'{"data": { "producer": "'+ ref_producers[0] +'", "jurisdictions": ['
			+ str(int(jur[0])) +'] }}', "-p", ref_producers[0]])
			summary.equal(0, resINT)
			if resINT:
				log.info(resSTR)

			if len(jurisdictions_tests) + 1 == jur_idx:
				jur_idx = 0
			jur_idx += 1

			log.info("Instantly make transaction on updated jurisdiction")
			resINT, resSTR = cluster.nodes[0].make_cleos_call(["push", "action",
			 "-u", "[{}]".format(jur_idx), "eosio.token",
			"transfer", '["{}", "eosio.null", "1000.0000 BTS", "ice-creams" ]'.format(ref_producers[0]),
			"-p", "{}".format(ref_producers[0]), "-j"])
			summary.equal(0, resINT)
			if resINT:
				log.info(resSTR)
			

		#Exception may appear if it's impossible to connect to nodeos
		counter = 0
		same_blocks = 12
		try:
			last_block = int(api_rpc_caller.chain.get_info()["head_block_num"])
			log.info("Checking is blockchain still on go [60 seconds]")
			for _ in range(2 * 12 * len(cluster.producers)):
				time.sleep(0.5)
				act_block = int(api_rpc_caller.chain.get_info()["head_block_num"])
				if act_block != last_block:
					counter = 0
					log.info("Still on go: {} block".format(act_block))
				else:
					counter += 1
					log.info("Oooops! counter: {}".format(counter))
					if counter >= same_blocks:
						summary.equal("ONLINE", "OFFLINE") #implementation from 16.09.2019
						#summary.equal("OFFLINE", "OFFLINE")
						break
				last_block = act_block
		except Exception as e:
			summary.equal("ONLINE", "OFFLINE") #implementation from 16.09.2019
			#summary.equal("OFFLINE", "OFFLINE")

		if counter < same_blocks:
			summary.equal("ONLINE", "ONLINE") #implementation from 16.09.2019
			#summary.equal("OFFLINE", "ONLINE")

		if counter >= same_blocks:
			assert "ONLINE" == "OFFLINE"
		else:
			cluster.bios.wait_for_last_irreversible_block()

		log.info(resSTR)
		resINT, resSTR = cluster.bios.make_cleos_call(["get", "transaction", "{}".format(json.loads(resSTR)["trx_id"])])
		
		summary.equal(True, resINT != 0)

		if resINT:
			log.info("Exit code: {}".format(resINT))
			log.info("Return String: {}".format(resSTR))
		
		#3040011 - error code that appears on not found transaction
		summary.equal(True, resSTR.find("3040011") != -1)

	except Exception as _ex:
		log.exception(_ex)
		summary.equal(False, True, "Exception occured durring testing: {}.".format(_ex))
	finally:
		status = summary.summarize()
		cluster.stop_all()
		exit(status)

