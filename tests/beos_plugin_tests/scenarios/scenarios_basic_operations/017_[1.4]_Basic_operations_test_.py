#!/usr/bin/python3

# Scenario based on test : [1.4]-Basic-operations-test

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
		accounts = node.create_accounts(1, "5.0000 PXBTS")
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 PXBTS"], 10, [15,0,30,5,8000000], [15,0,30,5,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 15,
				"next_block" : 0, 
				"ending_block" : 30,
				"block_interval" : 5, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 15,
				"next_block" : 0, 
				"ending_block" : 30,
				"block_interval" : 5, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 PXBTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":10
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aav",_quantity="5.0000 PXBTS",_memo=""), ActionResult(False, "") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="5.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.action_status(node.issue(_from="beos.gateway",_to=accounts[0].name,_quantity="0.0000 PXBTS",_memo=""), ActionResult(False, "must issue positive quantity") )
		node.wait_till_block(16)
		summary.action_status(node.issue(_from="beos.gateway",_to=accounts[0].name,_quantity="-1.0000 PXBTS",_memo=""), ActionResult(False, "must issue positive quantity") )
		node.wait_till_block(18)
		summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aav",_quantity="-1.0000 PXBTS",_memo=""), ActionResult(False, "must issue positive quantity") )
		node.wait_till_block(20)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="5.0000 PXBTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		node.wait_till_block(25)
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="-20.0000 PXBTS",_memo="_memo"), ActionResult(False, "must withdraw positive quantity") )
		node.wait_till_block(30)
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
		node.wait_till_block(32)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="5.0000 PXBTS",_net_weight="1835608015.6896 BEOS",_cpu_weight="1835608015.6900 BEOS",_ram_bytes=31992305448))
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="_memo") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="1835608015.6896 BEOS",_cpu_weight="1835608015.6900 BEOS",_ram_bytes=31992305448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)