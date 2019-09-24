#!/usr/bin/python3

# Scenario based on test : [1.7]-Issues-done-by-other-normal-user

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
		accounts   = node.create_accounts(2)
		producers = node.create_producers(1)
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 10, [25,0,34,5,8000000], [25,0,34,5,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 25,
				"next_block" : 0, 
				"ending_block" : 34,
				"block_interval" : 5, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 25,
				"next_block" : 0, 
				"ending_block" : 34,
				"block_interval" : 5, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":10
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="10.0000 BTS",_memo="",_from="beos.gateway") )
		summary.action_status(node.issue(_to=producers[0].name,_quantity="10.0000 BTS",_memo="",_from="beos.gateway") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="10.0000 BTS",_memo="",_from=accounts[0].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.action_status(node.issue(_to=accounts[1].name,_quantity="10.0000 BTS",_memo="",_from=accounts[0].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="10.0000 BTS",_memo="",_from=accounts[1].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.action_status(node.issue(_to=accounts[1].name,_quantity="10.0000 BTS",_memo="",_from=accounts[1].name), ActionResult(False, "missing authority of beos.gateway") )
		node.wait_till_block(28)
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		node.wait_till_block(38)
		summary.action_status(node.regproducer(_producer=producers[0].name,_producer_key=producers[0].akey,_url="test.html",_location=0) )
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="10.0000 BTS",_memo="",_from=accounts[0].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.action_status(node.issue(_to=accounts[1].name,_quantity="10.0000 BTS",_memo="",_from=accounts[0].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="10.0000 BTS",_memo="",_from=accounts[1].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="10.0000 BTS",_memo="",_from=producers[0].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.action_status(node.issue(_to=accounts[1].name,_quantity="10.0000 BTS",_memo="",_from=producers[0].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.action_status(node.issue(_to=producers[0].name,_quantity="10.0000 BTS",_memo="",_from=accounts[0].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.action_status(node.issue(_to=producers[0].name,_quantity="10.0000 BTS",_memo="",_from=accounts[1].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.action_status(node.issue(_to=producers[0].name,_quantity="10.0000 BTS",_memo="",_from=producers[0].name), ActionResult(False, "missing authority of beos.gateway") )
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="10.0000 BTS",_memo="") )
		summary.action_status(node.withdraw(_from=producers[0].name,_bts_to="any_account",_quantity="10.0000 BTS",_memo="") )
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)