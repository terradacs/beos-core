#!/usr/bin/python3

# Scenario based on test : [5.8]-Test-of-issue,-transfer-and-withdraw

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
		accounts = node.create_accounts(2, "20.0000 PXBTS")
		node.run_node()	
		#Changeparams
		#node.changeparams(["0.0000 PXBTS"], 190, [55,0,60,5,8000000], [55,0,60,5,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 55,
				"next_block" : 0, 
				"ending_block" : 60,
				"block_interval" : 5, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 55,
				"next_block" : 0, 
				"ending_block" : 60,
				"block_interval" : 5, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 PXBTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":190
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.transfer(_from=accounts[0].name,_to=accounts[1].name,_quantity="20.0000 PXBTS",_memo=" internal transfer 0"), ActionResult(False, "transaction net usage is too high") )
		node.wait_till_block(55)
		summary.action_status(node.transfer(_from=accounts[0].name,_to=accounts[1].name,_quantity="20.0000 PXBTS",_memo=" internal transfer 1") )
		node.wait_till_block(62)
		summary.action_status(node.transfer(_from=accounts[1].name,_to=accounts[0].name,_quantity="20.0000 PXBTS",_memo=" internal transfer 2") )
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="") )
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="") )
		summary.action_status(node.transfer(_from=accounts[0].name,_to=accounts[1].name,_quantity="20.0000 PXBTS",_memo=" internal transfer 3"), ActionResult(False, "no balance object found") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=7998080448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="1376706011.7673 BEOS",_cpu_weight="1376706011.7674 BEOS",_ram_bytes=23994230448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)