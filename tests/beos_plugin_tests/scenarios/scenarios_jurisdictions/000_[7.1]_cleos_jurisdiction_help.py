#!/usr/bin/python3

import os
import sys
import time
import datetime 
import requests
import json

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

def names(aDistance):
    nameResult = ""
    for i in range(3):
        nameResult+=chr(97+aDistance)
    
    return nameResult

def lotsOfRecords(amount):
    toReturn = ''
    for i in range(amount):
        toReturn += '{ "new_code": '+str(i)+', "new_name": "sampleName'+str(i)+'", "new_description": "sampleDescription'+str(i)+'"}'
        if i + 1 != amount:
            toReturn += ', '
        
    return toReturn
    
def longNames(length):
    toReturn = ''
    for i in range(length):
        toReturn += 'x'
    
    return toReturn

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
		node.wait_till_block(25)

        #Checking is there no jurisdictions
		rpc = node.get_url_caller()
		response = rpc.chain.get_table_rows({"scope":"eosio", "code":"eosio", "table":"infojurisdic", "json": True})
		log.info(f"response {response}")
		summary.equal(True, len(response["rows"]) == 0, "There should be no jurisdictions.")
		
		# len({ ID, name, description }) == 3
		data_per_one_jur = 3
		
		#PREPARING
		
		node.make_cleos_call(["push", "action", "eosio", "addjurisdict", '[ "eosio", 1, "Wakanda", "country1" ]', "-p", "eosio"])
		node.make_cleos_call(["push", "action", "eosio", "addjurisdict", '[ "eosio", 2, "Asgard", "country2" ]', "-p", "eosio"])
		node.make_cleos_call(["push", "action", "eosio", "addjurisdict", '[ "eosio", 3, "Hala", "country3" ]', "-p", "eosio"])

		#TESTING
		#get all_jurisdicions
		resINT, resSTR = node.make_cleos_call(["get", "all_jurisdictions"])
		summary.equal(3, len(json.loads(resSTR)["jurisdictions"]), "There should be 3 jurisdictions")
		
		#get active_jurisdictions
		resINT, resSTR = node.make_cleos_call(["push", "action", "eosio", "updateprod",
		'{ "data": { "producer": "eosio", "jurisdictions": [1,2]}}', "-p", "eosio" ])

		resINT, resSTR = node.make_cleos_call(["get", "active_jurisdictions"])
		summary.equal(2, len(json.loads(resSTR)["jurisdictions"]), "There should be 2 active jurisdictions")

		#get producer_jurisdiction
		resINT, resSTR = node.make_cleos_call(["get", "producer_jurisdiction", '[ "eosio" ]'])
		summary.equal(2, len(json.loads(resSTR)["producer_jurisdictions"][0]["jurisdictions"]), "This producer, should have onl 2 jurisdictions")

		#get all_producer_jurisdiction_for_block
		node.wait_till_block(250)
		resINT, resSTR = node.make_cleos_call(["get", "all_producer_jurisdiction_for_block", "250"])
		summary.equal(True, resSTR.find("eosio") != -1, "There should be 'eosio' user")

		#get producer_jurisdiction_for_block
		resINTv2, resSTRv2 = node.make_cleos_call(["get", "producer_jurisdiction_for_block", "eosio", "250"])
		summary.equal(True, resSTR == resSTRv2)

		#get producer_jurisdiction_history
		node.wait_n_blocks(50)
		resINT, resSTR = node.make_cleos_call(["push", "action", "eosio", "updateprod",
		'{ "data": { "producer": "eosio", "jurisdictions": [3]}}', "-p", "eosio"])
		node.wait_n_blocks(50)

		t2 = datetime.datetime.now() - datetime.timedelta(days=1)
		t3 = datetime.datetime.now() + datetime.timedelta(days=1)

		resINT, resSTR = node.make_cleos_call(["get", "producer_jurisdiction_history", "eosio",
											   t2.strftime("%Y-%m-%dT%H:%M:%S"), t3.strftime("%Y-%m-%dT%H:%M:%S")])
		summary.equal(2, resSTR.count('"eosio"'), "History should contains 2 records from 'eosio' user")
		
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
		summary.equal(False, True, "Exception occured durring testing.")

	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)
