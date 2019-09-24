#!/usr/bin/python3.6

import os
import sys
import time
import datetime
import requests
import json
import random

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, start_cluster, ActionResult, ResourceResult, VotersResult

CONST_FEE_AMOUNT = 1000
cleos_result = { 0, "" }

if __name__ == "__main__":

	number_of_pnodes  = 2
	producer_per_node = 4
	cluster, summary, args, log = start_cluster(__file__, number_of_pnodes, producer_per_node)

	try:
		# code, mess = cluster.bios.make_cleos_call(["get", "info"])
		block_offset = int(json.loads(cluster.bios.make_cleos_call(["get", "info"])[1])["head_block_num"]) + 30
		newparams = {
			"beos" : {
				"starting_block" : block_offset + 20,
				"next_block" : 0, 
				"ending_block" : block_offset + 40,
				"block_interval" : 2, 
				"trustee_reward" : 0
			},
			"ram" : {
				"starting_block" : block_offset + 20,
				"next_block" : 0, 
				"ending_block" : block_offset + 40,
				"block_interval" : 5, 
				"trustee_reward" : 0 
			},
			"proxy_assets" : [ "0.0000 BTS" ],
			"ram_leftover" : 300000,
			"starting_block_for_initial_witness_election":10
		}

		cluster.bios.changeparams(newparams)

		users = [ "xxx", "yyy", "zzz" ]

		test_prod = cluster.create_mock_producer(summary)

		resINT, _ = cluster.bios.make_cleos_call(["push", "action", "eosio.token", "issue", 
		'[ "{}", "100.0000 BTS", "sample description" ]'.format(test_prod), "-p", "beos.gateway"])

		log.info("Waiting till {} block....".format(block_offset + 60))

		creation_key = json.loads(cluster.bios.make_cleos_call(["wallet", "keys"])[1])[0]

		for var in users:
			resINT, _ = cluster.bios.make_cleos_call(["create", "account", "beos.gateway", var, creation_key, creation_key, "--transfer-ram"])
			summary.equal(0, resINT)
			resINT, _ = cluster.bios.make_cleos_call(["push", "action", "eosio.token", "issue", 
			'[ "{}", "100.0000 BTS", "sample description" ]'.format(var), "-p", "beos.gateway"])
			summary.equal(0, resINT)

		cluster.bios.wait_till_block(block_offset + 60)
		assert cluster.reg_mock_producer(test_prod, summary)
		cluster.bios.wait_for_last_irreversible_block()

		call = [ "system", "voteproducer", "prods", "a" ]
		prods = sorted(cluster.producers.keys())
		call.extend(prods)

		act_prod = json.loads(cluster.bios.make_cleos_call(["get", "info"])[1])["head_block_producer"]
		while act_prod == json.loads(cluster.bios.make_cleos_call(["get", "info"])[1])["head_block_producer"]:
			cluster.bios.wait_n_blocks(1)
		
		cluster.bios.wait_n_blocks(2)

		for var in users:
			tmp = list(call.copy())
			tmp[3] = var
			resINT, resSTR = cluster.bios.make_cleos_call(tmp)
			summary.equal(0, resINT)
			if resINT:
				log.info(resSTR)


		log.info("Waiting 3 minutes to make schedule stable")
		time.sleep(180)
		while test_prod != json.loads(cluster.bios.make_cleos_call(["get", "info"])[1])["head_block_producer"]:
			cluster.bios.wait_n_blocks(1)

		cluster.bios.wait_for_last_irreversible_block()
		cluster.bios.wait_n_blocks(1)

		resINT, _ = cluster.bios.make_cleos_call([ "push", "action", "eosio", "addjurisdict",
		'[ "eosio", 1, "testjur", "hehe" ]', "-p", "eosio" ])

		summary.equal(0, resINT)
		ip = cluster.producers[test_prod]["node"].node_data.node_ip
		port = cluster.producers[test_prod]["node"].node_data.node_port
		_url = "http://{}:{}/v1/gps/update_jurisdictions".format( ip , port )
		_headers = {'content-type': 'application/json; charset=UTF-8'}
		_data = {"jurisdictions" : [ 1 ]}
		result = requests.post(url=_url, data=json.dumps(_data), headers=_headers)

		log.info(result.content)
		assert json.loads(str(result.text))["done"]

		result = json.loads(cluster.bios.make_cleos_call(["get", "account", test_prod, "-j"])[1])
		
		counter = 3.9
		resINT = 1.0
		while resINT != 0:
			resINT,_ = cluster.bios.make_cleos_call([
				"push", "action", "eosio", "undelegatebw",
				'[ "{}", "{}", "{:.4f} BEOS", "{:.4f} BEOS" ]'.format(test_prod, test_prod, 
				(float(result["net_weight"])/ 10000) - 5 , (float(result["cpu_weight"])/ 10000) - counter - 15 ),
				"-p", test_prod ])
			log.info(_)
			counter +=0.0010
			assert counter < 20.0, "too long, something goes wrong"

		log.info("wait 40 seconds")
		cluster.bios.wait_n_blocks(80)

		resINT, resSTR = cluster.bios.make_cleos_call(["get", "producer_jurisdiction", '[ "{}" ]'.format(test_prod)])
		summary.equal(0, resINT)
		try:
			summary.equal(0, len(json.loads(resSTR)["producer_jurisdictions"][0]["jurisdictions"]))
		except IndexError as e:
			summary.equal(0, 0)

		path_to_logs = "/".join([ str(currentdir), "logs", os.path.basename(__file__)]) + "/"
		path_to_logs = path_to_logs.replace("[", r'\[')
		path_to_logs = path_to_logs.replace("]", r'\]')
		result = 0
		passphrase = "Change of jurisdictions failed"

		#Checking is passphrase exist in logs, by counting how many times passphrase appear in logs
		#cat - show file
		#grep - find in stream (and show lines with searching phrase)
		#wc -l - count how many lines appear in stream
		for node in cluster.nodes:
			command = 'cat {} | grep "{}" | wc -l'.format(path_to_logs+"node*{}*".format(node.node_data.node_port), passphrase)
			command = os.popen(command).read()
			result += int(command)
			log.info(command)

		summary.equal(True, result > 0, "result should be greater than 0, now is: {}".format(result))

	except Exception as _ex:
		log.exception(_ex)
		summary.equal(False, True, "Exception occured durring testing.")
	finally:
		status = summary.summarize()
		cluster.stop_all()
		exit(status)