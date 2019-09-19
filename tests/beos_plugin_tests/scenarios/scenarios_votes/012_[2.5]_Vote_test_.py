#!/usr/bin/python3

# Scenario based on test : [2.5]-Vote-test

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
		producers = node.create_producers(2)
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 10, [15,0,20,5,2000000], [15,0,20,5,1000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 15,
				"next_block" : 0, 
				"ending_block" : 20,
				"block_interval" : 5, 
				"trustee_reward" : 2000000
			},
			"ram" : {
				"starting_block" : 15,
				"next_block" : 0, 
				"ending_block" : 20,
				"block_interval" : 5, 
				"trustee_reward" : 1000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":10
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.issue(_from="beos.gateway",_to=producers[0].name,_quantity="10.0000 BTS",_memo="") )
		node.wait_till_block(21)
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="10.0000 BTS",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
		summary.action_status(node.regproducer(_producer=producers[0].name,_producer_key=producers[0].akey,_url="test.html",_location=0) )
		summary.action_status(node.regproducer(_producer=producers[1].name,_producer_key=producers[1].akey,_url="test.html",_location=0), ActionResult(False, "transaction net usage is too high: 152 > 0") )
		summary.action_status(node.withdraw(_from=producers[0].name,_bts_to="any_account",_quantity="10.0000 BTS",_memo="_memo") )
		
		#At end
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)