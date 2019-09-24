#!/usr/bin/python3

import os
import sys
import time
import datetime
import requests
import json

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, start_cluster, ActionResult, ResourceResult, VotersResult

def extract(resSTR):
	resSTR = resSTR.replace("producer_jurisdictions", "").replace(
		"\"", "").replace(":", "").replace("[", "").replace("]", "")
	resSTR = resSTR.replace("{", "").replace("}", "").replace(
		"code", "", ).replace("name", "").replace("description", "")
	resSTR = resSTR.replace("eosio", "").replace("jurisdictions", "").replace(
		"producer", "").replace(" ", "").replace(",", " ")
	return resSTR

def generate_names_array(amount):
    counter = 100000
    to_return = []
    for i in range(amount):
        to_return.append("a" + str(counter))
        counter += 1
    return '\"'+"\", \"".join(to_return)+"\""

def long_names(length : int, word : str = "x"):
    return word*length

number_of_pnodes = 3
producer_per_node = 1


if __name__ == "__main__":
	
	cluster, summary, args, log = start_cluster(
		__file__, number_of_pnodes, producer_per_node)
	
	try:
		# cluster.run_all()
		
		code, mess = cluster.bios.make_cleos_call( ["get", "info"] )
		log.info("Bios: code: {0}, mess {1}\n".format(code, mess))
		block_offset = int(json.loads(cluster.bios.make_cleos_call(["get", "info"])[1])["head_block_num"]) + 30
		newparams = {
			"beos": {
				"starting_block": block_offset + 20,
				"next_block": 0,
				"ending_block": block_offset + 50,
				"block_interval": 1,
				"trustee_reward": 10000
			},
			"ram": {
				"starting_block": block_offset + 20,
				"next_block": 0,
				"ending_block": block_offset + 50,
				"block_interval": 1,
				"trustee_reward": 100
			},
			"proxy_assets": ["0.0000 BTS"],
			"ram_leftover": 300000,
			"starting_block_for_initial_witness_election": 10
		}

		for node in cluster.nodes:
			node.changeparams(newparams)
			node.wait_n_blocks(1)

		for node in cluster.nodes:
			code, mess = cluster.bios.make_cleos_call(["get", "info"])
			log.info("Nodes: code: {0}, mess {1}\n".format(code, mess))

		prods = []
		for prod, data in cluster.producers.items():
			prods.append(prod)

		node = cluster.nodes[0]
		
		node.wait_till_block(19)
		
		cluster.bios.make_cleos_call(
			["push", "action", "eosio", "addjurisdict", '[ "eosio", 1, "Wakanda", "country1" ]', "-p", "eosio"])
		cluster.bios.make_cleos_call(
			["push", "action", "eosio", "addjurisdict", '[ "eosio", 2, "Asgard", "country2" ]', "-p", "eosio"])
		cluster.bios.make_cleos_call(
			["push", "action", "eosio", "addjurisdict", '[ "eosio", 3, "Hala", "country3" ]', "-p", "eosio"])

		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio", "updateprod",
											   '{ "data": { "producer": "eosio", "jurisdictions": [1,2]}}', "-p",
											   "eosio"])

		resINT, resSTR = cluster.bios.make_cleos_call(["wallet", "keys"])
		list_of_keys = json.loads(resSTR)

		resINT, resSTR = cluster.bios.make_cleos_call(["create", "account",
		 "beos.gateway", "aaaa", list_of_keys[0], list_of_keys[0],
		 "--transfer-ram"])

		resINT, resSTR = cluster.bios.make_cleos_call(["create", "account",
		 "beos.gateway", "bbbb", list_of_keys[1], list_of_keys[1],
		 "--transfer-ram"])

		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio.token",
		 "issue", '[ "aaaa", "500.0000 BTS", "alooo" ]', "-p", "beos.gateway"])

		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio.token",
		 "issue", '[ "bbbb", "500.0000 BTS", "alooo" ]', "-p", "beos.gateway"])
		
		log.info("waiting for: {} block".format(block_offset + 71))
		node.wait_till_block(block_offset + 71)
		
		summary.action_status(node.voteproducer(_voter="aaaa", _proxy="", _producers=[prods[1], prods[2]]))
		summary.action_status(node.voteproducer(_voter="bbbb", _proxy="", _producers=[prods[0]]))

		node.wait_n_blocks(13*number_of_pnodes*producer_per_node)

		cluster.bios.make_cleos_call( [ "push", "action", "eosio", "undelegatebw", '[ "aaaa", "aaaa", "1.0000 BEOS", "1.0000 BEOS" ]', "-p", "aaaa" ] )
		cluster.bios.make_cleos_call( [ "push", "action", "eosio", "undelegatebw", '[ "bbbb", "bbbb", "1000000.0000 BEOS", "1000000.0000 BEOS" ]', "-p", "bbbb" ] )

		cluster.accelerate_nodes( _type = "d", _time = "4")

		node.wait_n_blocks(15)
		
		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio", "refund", '[ "aaaa" ]', "-p", "aaaa"])
		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio", "refund", '[ "bbbb" ]', "-p", "bbbb"])

		resINT, resSTR = cluster.bios.make_cleos_call(["get", "account", "aaaa" ])
		resINTv2, resSTR_currency_before_a = cluster.bios.make_cleos_call(["get", "currency", "balance", "eosio.token", "aaaa" ])
		
		resINT, resSTR = cluster.bios.make_cleos_call(["get", "account", "bbbb" ])
		resINTv2, resSTR_currency_before_b = cluster.bios.make_cleos_call(["get", "currency", "balance", "eosio.token", "bbbb" ])

		cluster.nodes[0].wait_n_blocks(2)

		resINT, resSTR = cluster.bios.make_cleos_call( ["push", "action", "eosio", "addjurisdict", '["aaaa", 5, "aaaaland", "desc" ]', "-p", "aaaa" ] )
		summary.equal(True, resINT != 0, "action shouldn't success")

		resINT, resSTR = cluster.bios.make_cleos_call( ["push", "action", "eosio", "addjurisdict", '["bbbb", 6, "bbbbland", "desc" ]', "-p", "bbbb" ] )
		summary.equal(0, resINT, "action should success")

		#check is there onlu 2 jurisdictions

		rpc = node.get_url_caller()
		response = rpc.chain.get_table_rows({"scope":"eosio", "code":"eosio", "table":"infojurisdic", "json": True})
		summary.equal(4, len(response["rows"]), "There should be 4 jurisdictions.")

		#check is fee has been charged

		resINTv2, resSTR_currency_after_a = cluster.bios.make_cleos_call(["get", "currency", "balance", "eosio.token", "aaaa" ])
		resINTv2, resSTR_currency_after_b = cluster.bios.make_cleos_call(["get", "currency", "balance", "eosio.token", "bbbb" ])

		summary.equal(resSTR_currency_after_a, resSTR_currency_before_a, "'aaaa' user shouldn't be charged")
		summary.equal(True, resSTR_currency_after_b != resSTR_currency_before_b, "'bbbb' user should be charged")

		# get producer_jurisdiction
		resINT, resSTR = cluster.bios.make_cleos_call(
			["get", "producer_jurisdiction", '[ {} ]'.format(generate_names_array(3000))])
		summary.equal(True, str(resSTR).find(
			"Query size is greater than query limit") != -1, "there should be error")
		summary.equal(True, resINT != 0, "this querry should crash")

		resINT, resSTR = cluster.bios.make_cleos_call(["get", "producer_jurisdiction", '[ "{}" ]'.format(long_names(2000))])
		summary.equal(True, str(resSTR).find("Invalid name") == -1, "there shouldn't be an error")
		summary.equal(True, resINT == 0, "this querry shouldn't crash")

		resINT, resSTR = cluster.bios.make_cleos_call(
			[ "get", "producer_jurisdiction", "1"])
		summary.equal(True, str(resSTR).find("Bad Cast")
					  != -1, "there should be error")
		summary.equal(True, resINT != 0, "this querry should crash")

		# get all_producer_jurisdiction_for_block
		resINT, resSTR = cluster.bios.make_cleos_call(
			["get", "all_producer_jurisdiction_for_block", long_names(10, "9999") ])
		summary.equal(True, str(resSTR).find("required valid integer as block number") != -1, "there should be error")
		summary.equal(True, resINT != 0, "this querry should crash")

		# get producer_jurisdiction_for_block
		resINT, resSTR = cluster.bios.make_cleos_call(
			["get", "producer_jurisdiction_for_block", "eosio", "eosio"])
		summary.equal(True, str(resSTR).find(
			"std::invalid_argument") != -1, "there should be error")
		summary.equal(True, resINT != 0, "this querry should crash")

		resINT, resSTR = cluster.bios.make_cleos_call(
			["get", "producer_jurisdiction_for_block", "eosio", long_names(10, "9999") ])
		summary.equal(True, str(resSTR).find("required valid integer as block number") != -1, "there should be error")
		summary.equal(True, resINT != 0, "this querry should crash")

		# get producer_jurisdiction_history
		resINT, resSTR = cluster.bios.make_cleos_call(
			["get", "producer_jurisdiction_history", "eosio", "fafwadf", "wfafwafw"])
		summary.equal(True, str(resSTR).find("bad lexical cast")
					  != -1, "there should be error")
		summary.equal(True, resINT != 0, "this querry should crash")
		
		#cluster.bios.stop_node()
	except Exception as _ex:
		log.exception(_ex)
	finally:
		summary_status = summary.summarize()
		cluster.stop_all()
		exit(summary_status)