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
			["2", "RUSSIA", "EAST EUROPE"],
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

		cluster.bios.wait_for_another_producer( ref_producers[0] )

		jur_idx = len(jurisdictions_tests) + 1
		results = []
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
			results.append(resSTR)
			summary.equal(0, resINT)
			if resINT:
				log.info(resSTR)

		nr_cycles_for_every_producer = 2
		cycle_length = 12
		nr_blocks = len(cluster.producers) * cycle_length * nr_cycles_for_every_producer
		try:
			log.info("Wait for {} blocks".format( nr_blocks ))
			for _ in range( nr_blocks ):
				print( "block nr: {}".format( api_rpc_caller.chain.get_info()["head_block_num"] ) )
				time.sleep(0.5)
		except Exception as _ex:
			log.exception(_ex)
			summary.equal(False, True, "Exception occured durring testing.")

		for res in results:
			log.info(res)
			resINT, resSTR = cluster.bios.make_cleos_call(["get", "transaction", "{}".format(json.loads(res)["trx_id"])])
			log.info(resSTR)
			summary.equal(0, resINT)

	except Exception as _ex:
		log.exception(_ex)
		summary.equal(False, True, "Exception occured durring testing: {}.".format(_ex))
	finally:
		status = summary.summarize()
		cluster.stop_all()
		exit(status)

