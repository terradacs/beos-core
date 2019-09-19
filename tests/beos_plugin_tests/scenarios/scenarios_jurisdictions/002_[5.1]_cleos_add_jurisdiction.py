#!/usr/bin/python3

import os
import sys
import time
import datetime 
import requests

if os.path.exists(os.path.dirname(os.path.abspath(__file__))+ "/logs/"+ __file__):
    exit(0)

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)
		producers = node.create_producers(2, "1000.0000 BTS")
		node.run_node()

		newparams = {
			"beos" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 20,
				"block_interval" : 10, 
				"trustee_reward" : 1000000
			},
			"ram" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 20,
				"block_interval" : 10, 
				"trustee_reward" : 0 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 300000,
			"starting_block_for_initial_witness_election":10
		}

		node.changeparams(newparams)

		#WAIT FOR FOR STAKED NET
		node.changeparams(newparams)
		node.wait_till_block(25)

		rpc = node.get_url_caller()
		response = rpc.chain.get_table_rows({"scope":"eosio", "code":"eosio", "table":"infojurisdic", "json": True})
		log.info("response {0}".format(response))

		summary.equal(True, len(response["rows"]) == 0, "There should be no jurisdictions.")

		node.wait_n_blocks(5)
		code, mess = node.make_cleos_call(["push", "action", "eosio", "addjurisdict", '[ "eosio", "0", "POLAND", "EAST EUROPE" ]', "-p", "eosio"])
		log.info("Code {0} mess {1}".format(code,mess))

		node.wait_n_blocks(5)
		response = rpc.chain.get_table_rows({"scope":"eosio", "code":"eosio", "table":"infojurisdic", "json": True})
		log.info("response {0}".format(response))

		summary.equal(True, len(response["rows"]) == 1, "There should be one jurisdiction.")
		summary.equal(True, response["rows"][0]["name"].lower() == "POLAND".lower(), "Name of the jurisdiction should be `POLAND`")
		summary.equal(True, response["rows"][0]["description"].lower() == "EAST EUROPE".lower(), "Description of the jurisdiction should be `EAST EUROPE`")
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
		summary.equal(False, True, "Exception occured durring testing.")
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)