#!/usr/bin/python3

# Scenario based on test : [6.2]-Undelegatebw---after-distribution-period---to-self,-with-voting

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
		producers = node.create_producers(1, "5.0000 BTS")
		node.run_node()	
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 1, [10,0,30,5,8000000], [10,0,20,5,5000000], 3000000)
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
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":1
		}
		node.changeparams(newparams)
		
		#Actions
		node.wait_till_block(15)
		summary.action_status(node.voteproducer(_voter=producers[0].name,_proxy="",_producers=[producers[0].name]), ActionResult(False, "producer is not registered") )
		node.wait_till_block(16)
		summary.action_status(node.regproducer(_producer=producers[0].name,_producer_key=producers[0].akey,_url="test3.html",_location="0") )
		node.wait_till_block(35)
		summary.action_status(node.undelegatebw(_from=producers[0].name,_receiver=producers[0].name,_unstake_net_quantity="1.0000 BEOS",_unstake_cpu_quantity="1.0000 BEOS"), ActionResult(False, "cannot undelegate bandwidth until the chain is activated (at least 15% of all tokens participate in voting)") )
		summary.action_status(node.withdraw(_from=producers[0].name,_bts_to="any_account",_quantity="5.0000 BTS",_memo="") )
		
		#At end
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="",_net_weight="1835608015.6896 BEOS",_cpu_weight="1835608015.6900 BEOS",_ram_bytes=31992305448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)