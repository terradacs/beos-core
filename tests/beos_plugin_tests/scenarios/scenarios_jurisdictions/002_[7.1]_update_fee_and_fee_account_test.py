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

CONST_ORGINAL_FEE_VALUE_INT = 1000
CONST_ORGINAL_FEE_VALUE_STRING = "1000.0000 BEOS"

if __name__ == "__main__":
	
	cluster, summary, args, log = start_cluster(__file__, number_of_pnodes, producer_per_node)
	
	try:
		def get_currency_balance( src : str = "aaaa" ):
			_, src = cluster.bios.make_cleos_call(["get", "currency", "balance", "eosio.token", src])
			summary.equal(0, _)
			src = src.replace('\r', '\n')
			if src[0] == '\n':
				src = src[1:]
			if src[len(src)-1] == '\n':
				src = src[:-1]
			tab = src.split("\n")
			results = dict()
			for var in tab:
				temp = var.split(" ")
				results[temp[1]] = float(temp[0])
			return results

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

		#Preparation

		# for node in cluster.nodes:
		# 	node.changeparams(newparams)
		# 	node.wait_n_blocks(1)

		cluster.bios.changeparams(newparams)

		for node in cluster.nodes:
			code, mess = cluster.bios.make_cleos_call(["get", "info"])
			log.info("Nodes: code: {0}, mess {1}\n".format(code, mess))

		prods = []
		for prod, data in cluster.producers.items():
			prods.append(prod)

		node = cluster.nodes[0]
		
		rpc = node.get_url_caller()
		response = rpc.chain.get_table_rows({"scope":"eosio", "code":"eosio", "table":"infojurisdic", "json": True})
		summary.equal(len(response["rows"]), 0, "There should be no jurisdictions.")

		node.wait_till_block(19)

		resINT, resSTR = cluster.bios.make_cleos_call(["wallet", "keys"])
		list_of_keys = extract(resSTR).split()

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
		node.wait_till_block( block_offset + 71)
		
		summary.action_status(node.voteproducer(_voter="aaaa", _proxy="", _producers=[prods[1], prods[2]]))
		summary.action_status(node.voteproducer(_voter="bbbb", _proxy="", _producers=[prods[0]]))

		node.wait_n_blocks(13*number_of_pnodes*producer_per_node)

		cluster.bios.make_cleos_call( [ "push", "action", "eosio", "undelegatebw", '[ "aaaa", "aaaa", "10000.0000 BEOS", "10000.0000 BEOS" ]', "-p", "aaaa" ] )
		cluster.bios.make_cleos_call( [ "push", "action", "eosio", "undelegatebw", '[ "bbbb", "bbbb", "10000.0000 BEOS", "10000.0000 BEOS" ]', "-p", "bbbb" ] )

		node.wait_n_blocks(100)
		cluster.accelerate_nodes( _type = "d", _time = "4")

		node.wait_n_blocks(15)
		
		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio", "refund", '[ "aaaa" ]', "-p", "aaaa"])
		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio", "refund", '[ "bbbb" ]', "-p", "bbbb"])

		cluster.nodes[0].wait_n_blocks(2)

		#Testing fee changing

		primary_state_aaaa = get_currency_balance("aaaa").get("BEOS")
		primary_state_bbbb = get_currency_balance("bbbb").get("BEOS")

		assert primary_state_aaaa != None, "no BEOS'es, impossible to continue"
		assert primary_state_aaaa != None, "no BEOS'es, impossible to continue"

		summary.equal(True, primary_state_aaaa > 3*CONST_ORGINAL_FEE_VALUE_INT, 
			"not enough BEOS'es. Minimum required: {}, {} provided".format(3*CONST_ORGINAL_FEE_VALUE_INT, primary_state_aaaa))
		summary.equal(True, primary_state_bbbb > 10*CONST_ORGINAL_FEE_VALUE_INT, 
			"not enough BEOS'es. Minimum required: {}, {} provided".format(10*CONST_ORGINAL_FEE_VALUE_INT, primary_state_bbbb))

		resINT, resSTR = cluster.bios.make_cleos_call( [ "push", "action", "eosio", "addjurisdict", 
		'[ "aaaa", 1, "a1", "description" ]', "-p", "aaaa" ] )
		summary.equal(0, resINT, "jurisdiction should be created without any troubles")
		log.info(resSTR)		

		summary.equal(primary_state_aaaa - CONST_ORGINAL_FEE_VALUE_INT, get_currency_balance("aaaa")["BEOS"], 
		"charged wrong amount of fee")

		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio", "updatejurfee",
		 '["{}.0000 BEOS"]'.format(2*CONST_ORGINAL_FEE_VALUE_INT), "-p", "eosio"])
		summary.equal(0, resINT, "something goes wrong during `updatejurfee`")
		log.info(resSTR)

		resINT, resSTR = cluster.bios.make_cleos_call( [ "push", "action", "eosio", "addjurisdict", 
		'[ "aaaa", 2, "a2", "description" ]', "-p", "aaaa" ] )
		summary.equal(0, resINT, "jurisdiction should be created without any troubles")
		log.info(resSTR)

		summary.equal(primary_state_aaaa - (3*CONST_ORGINAL_FEE_VALUE_INT), get_currency_balance("aaaa")["BEOS"], 
		"charged wrong amount of fee")

		#Reset to defaults

		resINT, resSTR = cluster.bios.make_cleos_call(["push", "action", "eosio", "updatejurfee",
		'[ "{}" ]'.format(CONST_ORGINAL_FEE_VALUE_STRING), "-p", "eosio"])
		summary.equal(0, resINT, "something goes wrong during `updatejurfee` [DEFAULTS]")
		log.info(resSTR)

		#Testing acount fee changing

		FIRST_JURISDICTION_ID = 4
		LAST_JURISDICTION_ID = 14

		secondary_state_aaaa = get_currency_balance("aaaa").get("BEOS")
		secondary_state_bbbb = get_currency_balance("bbbb").get("BEOS")

		resINT, resSTR = cluster.bios.make_cleos_call( [ "push", "action", "eosio", "updatejuracc", 
		'[ "aaaa" ]', "-p", "eosio" ] )
		summary.equal(0, resINT, "something goes wrong during `updatejuracc`")

		for i in range(FIRST_JURISDICTION_ID, LAST_JURISDICTION_ID):
			resINT, resSTR = cluster.bios.make_cleos_call( [ "push", "action", "eosio", "addjurisdict", 
			'[ "bbbb", {}, "b{}", "description" ]'.format(i,i), "-p", "bbbb" ] )
			summary.equal(0, resINT, "jurisdiction should be created without any troubles")

		cluster.nodes[0].wait_n_blocks(13)

		summary.equal(secondary_state_bbbb - (LAST_JURISDICTION_ID - FIRST_JURISDICTION_ID) * CONST_ORGINAL_FEE_VALUE_INT,
		get_currency_balance("bbbb")["BEOS"], "charged wrong amount of fee")

		summary.equal( secondary_state_aaaa + (LAST_JURISDICTION_ID - FIRST_JURISDICTION_ID) * CONST_ORGINAL_FEE_VALUE_INT, 
		get_currency_balance("aaaa")["BEOS"], "received wrong amount of fee")

		#cluster.bios.stop_node()
	except Exception as _ex:
		log.exception(_ex)
	finally:
		summary_status = summary.summarize()
		cluster.stop_all()
		exit(summary_status)
