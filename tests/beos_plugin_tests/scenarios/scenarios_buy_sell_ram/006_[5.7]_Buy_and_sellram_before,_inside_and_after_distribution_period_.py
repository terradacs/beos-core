#!/usr/bin/python3

# Scenario based on test : [5.7]-Buy-and-sellram-before,-inside-and-after-distribution-period

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
		accounts = node.create_accounts(2, "20.0000 BTS")
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 420, [10,0,30,10,8000000], [10,0,30,10,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 30,
				"block_interval" : 10, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 30,
				"block_interval" : 10, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":420
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.sellram(_account=accounts[0].name,_bytes="10000"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
		summary.action_status(node.buyram(_payer=accounts[0].name,_receiver=accounts[1].name,_quant="1.0000 BEOS"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
		node.wait_till_block(20)
		summary.action_status(node.sellram(_account=accounts[0].name,_bytes="10000"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
		node.wait_till_block(20)
		summary.action_status(node.buyram(_payer=accounts[0].name,_receiver=accounts[1].name,_quant="1.0000 BEOS"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
		node.wait_till_block(35)
		summary.action_status(node.sellram(_account=accounts[0].name,_bytes="10000") )
		summary.action_status(node.buyram(_payer=accounts[0].name,_receiver=accounts[1].name,_quant="10.0000 BEOS"), ActionResult(False, "overdrawn balance") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="20.0000 BTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996145448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="20.0000 BTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)