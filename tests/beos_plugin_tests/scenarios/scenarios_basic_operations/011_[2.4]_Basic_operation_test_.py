#!/usr/bin/python3

# Scenario based on test : [2.4]-Basic-operation-test

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
		accounts = node.create_accounts(2)
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 PXBTS"], 40, [20,0,35,15,2000000], [20,0,35,15,1000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 20,
				"next_block" : 0, 
				"ending_block" : 35,
				"block_interval" : 15, 
				"trustee_reward" : 2000000
			},
			"ram" : {
				"starting_block" : 20,
				"next_block" : 0, 
				"ending_block" : 35,
				"block_interval" : 15, 
				"trustee_reward" : 1000000 
			},
			"proxy_assets" : [ "0.0000 PXBTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":40
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.issue(_from="beos.gateway",_to=accounts[0].name,_quantity="10.0000 PXBTS",_memo="") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		node.wait_till_block(25)
		summary.action_status(node.transfer(_from=accounts[0].name,_to=accounts[1].name,_quantity="10.0000 PXBTS",_memo="any_memo") )
		node.wait_till_block(30)
		summary.action_status(node.transfer(_from=accounts[1].name,_to=accounts[0].name,_quantity="10.0000 PXBTS",_memo="any_memo"), ActionResult(False, "transaction net usage is too high: 136 > 0") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		node.wait_till_block(40)
		summary.action_status(node.transfer(_from=accounts[1].name,_to=accounts[0].name,_quantity="10.0000 PXBTS",_memo="any_memo") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)