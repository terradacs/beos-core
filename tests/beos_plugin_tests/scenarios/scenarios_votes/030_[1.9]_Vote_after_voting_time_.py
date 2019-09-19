#!/usr/bin/python3

# Scenario based on test : [1.9]-Vote-after-voting-time

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
		producers = node.create_producers(3)
		node.run_node()

		#Changeparams
		#node.changeparams(["0.0000 BTS"], 20, [10,0,20,10,8000000], [10,0,20,10,5000000], 3000000)
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
				"ending_block" : 20,
				"block_interval" : 10, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":20
		}
		node.changeparams(newparams)
		
		#Actions
		summary.action_status(node.issue(_to=producers[0].name,_quantity="5.0000 BTS",_memo="",_from="beos.gateway") )
		summary.action_status(node.issue(_to=producers[2].name,_quantity="5.0000 BTS",_memo="",_from="beos.gateway") )
		summary.action_status(node.regproducer(_producer=producers[2].name,_producer_key=producers[2].akey,_url="test0.html",_location=0), ActionResult(False, "") )
		summary.action_status(node.regproducer(_producer=producers[2].name,_producer_key=producers[2].akey,_url="test1.html",_location=0), ActionResult(False, "") )
		node.wait_till_block(25)
		summary.action_status(node.regproducer(_producer=producers[2].name,_producer_key=producers[2].akey,_url="test2.html",_location=0) )
		summary.action_status(node.regproducer(_producer=producers[2].name,_producer_key=producers[2].akey,_url="test3.html",_location=0) )
		summary.action_status(node.voteproducer(_voter=producers[1].name,_proxy="",_producers=[producers[2].name]), ActionResult(False, "") )
		summary.action_status(node.voteproducer(_voter=producers[0].name,_proxy="",_producers=[producers[2].name]) )
		summary.action_status(node.voteproducer(_voter=producers[2].name,_proxy="",_producers=[producers[2].name]) )
		summary.action_status(node.voteproducer(_voter=producers[2].name,_proxy="",_producers=[producers[0].name]), ActionResult(False, "") )
		summary.action_status(node.voteproducer(_voter=producers[2].name,_proxy="",_producers=[producers[1].name]), ActionResult(False, "") )
		summary.action_status(node.voteproducer(_voter=producers[1].name,_proxy="",_producers=[producers[1].name]), ActionResult(False, "") )
		summary.action_status(node.voteproducer(_voter=producers[0].name,_proxy="",_producers=[producers[0].name]), ActionResult(False, "") )
		summary.action_status(node.withdraw(_from=producers[0].name,_bts_to="any_account",_quantity="5.0000 BTS",_memo="") )
		summary.action_status(node.withdraw(_from=producers[2].name,_bts_to="any_account",_quantity="5.0000 BTS",_memo="") )
		
		#At end
		summary.user_block_status(node, producers[0].name, ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
		summary.user_block_status(node, producers[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		summary.user_block_status(node, producers[2].name, ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)