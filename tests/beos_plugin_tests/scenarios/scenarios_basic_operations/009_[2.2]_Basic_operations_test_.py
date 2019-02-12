#!/usr/bin/python3

# Scenario based on test : [2.2]-Basic-operations-test

import os
import sys
import time
import datetime 

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)
		accounts = node.create_accounts(1)
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 40, [25,0,30,5,2000000], [25,0,30,5,1000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 25,
				"next_block" : 0, 
				"ending_block" : 30,
				"block_interval" : 5, 
				"trustee_reward" : 2000000
			},
			"ram" : {
				"starting_block" : 25,
				"next_block" : 0, 
				"ending_block" : 30,
				"block_interval" : 5, 
				"trustee_reward" : 1000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":40
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="1.0000 BTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
		summary.action_status(node.issue(_from="beos.gateway",_to=accounts[0].name,_quantity="10.0000 BTS",_memo="") )
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="1.0000 BTS",_memo="_memo"), ActionResult(False, "transaction net usage is too high: 128 > 0") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		node.wait_till_block(35)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="10.0000 BTS",_memo="_memo") )
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="1.0000 BTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)