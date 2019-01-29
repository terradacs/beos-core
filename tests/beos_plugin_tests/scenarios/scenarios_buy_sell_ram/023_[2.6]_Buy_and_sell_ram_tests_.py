#!/usr/bin/python3

# Scenario based on test : [2.6]-Buy-and-sell-ram-tests

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
		accounts = node.create_accounts(2, "10.0000 PXBTS")
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 PXBTS"], 10, [10,0,15,5,4000000], [10,0,15,5,2000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 15,
				"block_interval" : 5, 
				"trustee_reward" : 4000000
			},
			"ram" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 15,
				"block_interval" : 5, 
				"trustee_reward" : 2000000 
			},
			"proxy_assets" : [ "0.0000 PXBTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":10
		}
		node.changeparams(newparams)
		
		#Actions
		node.wait_till_block(16)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804107.8448 BEOS",_cpu_weight="917804107.8450 BEOS",_ram_bytes=15997655448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804107.8448 BEOS",_cpu_weight="917804107.8450 BEOS",_ram_bytes=15997655448))
		summary.action_status(node.sellram(_account=accounts[0].name,_bytes="1000000") )
		summary.action_status(node.sellram(_account=accounts[1].name,_bytes="3000000") )
		summary.action_status(node.buyram(_payer=accounts[0].name,_receiver=accounts[0].name,_quant="0.0100 BEOS") )
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="917804107.8448 BEOS",_cpu_weight="917804107.8450 BEOS",_ram_bytes=15996655499))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="917804107.8448 BEOS",_cpu_weight="917804107.8450 BEOS",_ram_bytes=15994655448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)