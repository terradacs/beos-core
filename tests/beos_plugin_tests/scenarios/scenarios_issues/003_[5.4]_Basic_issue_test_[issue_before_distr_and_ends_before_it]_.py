#!/usr/bin/python3

# Scenario based on test : [5.4]-Basic-issue-test-[issue-before-distr-and-ends-before-it]

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
		accounts = node.create_accounts(2,"20.0000 PXBTS")
		node.run_node()	
		#Changeparams
		newparams = {
			"beos" : {
				"starting_block" : 1000,
				"next_block" : 0, 
				"ending_block" : 1001,
				"block_interval" : 10, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 1000,
				"next_block" : 0, 
				"ending_block" : 1001,
				"block_interval" : 4, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 PXBTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":410
		}

		node.changeparams(newparams)
		#node.changeparams(["0.0000 PXBTS"], 410, [1000,0,1001,10,8000000], [1000,0,1001,4,5000000], 3000000)
		
		#Actions
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="20.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="20.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)