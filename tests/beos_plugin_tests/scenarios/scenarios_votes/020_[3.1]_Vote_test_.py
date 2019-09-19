#!/usr/bin/python3

# Scenario based on test : [3.1]-Vote-test

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
		producers = node.create_producers(2, "5.0000 BTS")
		node.run_node()
		
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 1, [10,0,20,10,8000000], [10,0,18,4,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 20,
				"block_interval" : 10, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 18,
				"block_interval" : 4, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":1
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.regproducer(_producer=producers[0].name,_producer_key=producers[0].akey,_url="http://fake.html",_location=0), ActionResult(False, "transaction net usage is too high: 160 > 0") )
		summary.action_status(node.voteproducer(_voter=producers[1].name,_proxy="",_producers=[producers[1].name]), ActionResult(False, "user must stake before they can vote") )
		node.wait_till_block(11)
		summary.action_status(node.regproducer(_producer=producers[0].name,_producer_key=producers[0].akey,_url="http://fake.html",_location=0) )
		node.wait_till_block(12)
		summary.action_status(node.regproducer(_producer=producers[1].name,_producer_key=producers[1].akey,_url="http://fake.html",_location=0) )
		node.wait_till_block(15)
		summary.action_status(node.voteproducer(_voter=producers[1].name,_proxy="",_producers=[producers[0].name]) )
		summary.action_status(node.voteproducer(_voter=producers[0].name,_proxy="",_producers=[producers[1].name]) )
		node.wait_till_block(20)
		summary.action_status(node.withdraw(_from=producers[0].name,_bts_to="any_account",_quantity="5.0000 BTS",_memo="_memo") )
		summary.action_status(node.withdraw(_from=producers[1].name,_bts_to="any_account",_quantity="5.0000 BTS",_memo="_memo") )
		
		#At end
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.user_block_status(node, producers[1].name, ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)