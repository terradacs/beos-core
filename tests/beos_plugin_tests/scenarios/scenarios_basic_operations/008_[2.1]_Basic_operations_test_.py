#!/usr/bin/python3

# Scenario based on test : [2.1]-Basic-operations-test

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
		accounts = node.create_accounts(2, "5.0000 BTS")
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 40, [20,0,40,20,4000000], [20,0,40,20,2000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 20,
				"next_block" : 0, 
				"ending_block" : 40,
				"block_interval" : 20, 
				"trustee_reward" : 4000000
			},
			"ram" : {
				"starting_block" : 20,
				"next_block" : 0, 
				"ending_block" : 40,
				"block_interval" : 20, 
				"trustee_reward" : 2000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":40
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="1.0000 BTS",_memo="_memo"), ActionResult(False, "transaction net usage is too high: 128 > 0") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="5.0000 BTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="5.0000 BTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		node.wait_till_block(30)
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="1.0000 BTS",_memo="_memo") )
		node.wait_till_block(30)
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="5.0000 BTS",_memo="_memo") )
		node.wait_till_block(35)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="4.0000 BTS",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
		node.wait_till_block(35)
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
		node.wait_till_block(45)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="4.0000 BTS",_net_weight="1376706161.7673 BEOS",_cpu_weight="1376706161.7674 BEOS",_ram_bytes=23996480448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
		summary.action_status(node.issue(_from="beos.gateway",_to=accounts[1].name,_quantity="5.0000 BTS",_memo="") )
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="1.0000 BTS",_memo="_memo") )
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="40.0000 BTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
		summary.action_status(node.transfer(_from=accounts[1].name,_to=accounts[0].name,_quantity="4.0000 BTS",_memo="any_memo") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="8.0000 BTS",_net_weight="1376706161.7673 BEOS",_cpu_weight="1376706161.7674 BEOS",_ram_bytes=23996480448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="1.0000 BTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="2.0000 BTS",_memo="_memo") )
		summary.action_status(node.issue(_from="beos.gateway",_to=accounts[1].name,_quantity="5.0000 BTS",_memo="") )
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="1.0000 BTS",_memo="_memo") )
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="6.0000 BTS",_memo="_memo") )
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="4.0000 BTS",_memo="_memo") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="1376706161.7673 BEOS",_cpu_weight="1376706161.7674 BEOS",_ram_bytes=23996480448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)