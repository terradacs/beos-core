#!/usr/bin/python3

# Scenario based on test : [1.5]-Basic-operations-test

import os
import sys
import time
import datetime 

if os.path.exists(os.path.dirname(os.path.abspath(__file__))+ "/logs/"+ __file__):
    exit(0)

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)
		accounts = node.create_accounts(2)
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 10, [17,0,21,5,8000000], [15,0,18,5,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 17,
				"next_block" : 0, 
				"ending_block" : 21,
				"block_interval" : 5, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 15,
				"next_block" : 0, 
				"ending_block" : 18,
				"block_interval" : 5, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":10
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.issue(_from="beos.gateway",_to=accounts[0].name,_quantity="0.00001 BTS",_memo=""), ActionResult(False, "symbol precision mismatch") )
		summary.action_status(node.issue(_from="beos.gateway",_to=accounts[0].name,_quantity="0.0001 BTS",_memo="") )
		node.wait_till_block(22)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="0.0001 BTS",_net_weight="1835608015.6898 BEOS",_cpu_weight="1835608015.6898 BEOS",_ram_bytes=31992305448))
		node.wait_till_block(25)
		summary.action_status(node.transfer(_from=accounts[0].name,_to=accounts[1].name,_quantity="0.00001 BTS",_memo=""), ActionResult(False, "symbol precision mismatch") )
		summary.action_status(node.transfer(_from=accounts[0].name,_to=accounts[1].name,_quantity="-0.00001 BTS",_memo=""), ActionResult(False, "must transfer positive quantity") )
		summary.action_status(node.transfer(_from=accounts[0].name,_to=accounts[1].name,_quantity="-0.00001 BTS",_memo=""), ActionResult(False, "must transfer positive quantity") )
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="0.0001 BTS",_memo="_memo") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="1835608015.6898 BEOS",_cpu_weight="1835608015.6898 BEOS",_ram_bytes=31992305448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)