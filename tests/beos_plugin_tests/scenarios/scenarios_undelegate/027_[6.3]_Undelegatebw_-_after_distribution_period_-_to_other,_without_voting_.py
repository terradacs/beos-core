#!/usr/bin/python3

# Scenario based on test : [6.3]-Undelegatebw---after-distribution-period---to-other,-without-voting

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
		accounts = node.create_accounts(2, "5.0000 PXBTS")
		node.run_node()	
		#Changeparams
		#node.changeparams(["0.0000 PXBTS"], 1, [10,0,30,5,8000000], [10,0,20,5,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 30,
				"block_interval" : 5, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 20,
				"block_interval" : 5, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 PXBTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":1
		}
		node.changeparams(newparams)
		
		#Actions
		node.wait_till_block(35)
		summary.action_status(node.undelegatebw(_from=accounts[0].name,_receiver=accounts[1].name,_unstake_net_quantity="1.0000 BEOS",_unstake_cpu_quantity="1.0000 BEOS"), ActionResult(False, "") )
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="") )
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)