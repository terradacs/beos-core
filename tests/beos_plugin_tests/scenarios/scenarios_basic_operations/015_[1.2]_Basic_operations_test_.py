#!/usr/bin/python3

# Scenario based on test : [1.2]-Basic-operations-test

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
		accounts = node.create_accounts(1, "5.0000 BTS")
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 140, [20,0,25,10,1000000], [20,0,25,10,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 20,
				"next_block" : 0, 
				"ending_block" : 25,
				"block_interval" : 10, 
				"trustee_reward" : 1000000
			},
			"ram" : {
				"starting_block" : 20,
				"next_block" : 0, 
				"ending_block" : 25,
				"block_interval" : 10, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":140
		}
		node.changeparams(newparams)
		
		#Actions
		node.wait_till_block(20)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="5.0000 BTS",_net_weight="1835608365.6898 BEOS",_cpu_weight="1835608365.6898 BEOS",_ram_bytes=31992305448))
		node.wait_till_block(25)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="5.0000 BTS",_net_weight="1835608365.6898 BEOS",_cpu_weight="1835608365.6898 BEOS",_ram_bytes=31992305448))
		node.wait_till_block(30)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="5.0000 BTS",_net_weight="1835608365.6898 BEOS",_cpu_weight="1835608365.6898 BEOS",_ram_bytes=31992305448))
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="5.0000 BTS",_memo="_memo") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="1835608365.6898 BEOS",_cpu_weight="1835608365.6898 BEOS",_ram_bytes=31992305448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)