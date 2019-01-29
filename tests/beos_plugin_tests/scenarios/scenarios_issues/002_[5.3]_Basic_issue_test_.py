#!/usr/bin/python3

# Scenario based on test : [5.3]-Basic-issue-test

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
		accounts = node.create_accounts(2)
		node.run_node()
		
		#Changeparams
		newparams = {
			"beos" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 50,
				"block_interval" : 10, 
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
			"starting_block_for_initial_witness_election":140
		}

		node.changeparams(newparams)
		#node.changeparams(["0.0000 PXBTS"], 140, [10,0,50,10,8000000], [10,0,20,5,5000000], 3000000)
		
		#Actions
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
		node.wait_till_block(11)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="5.0000 PXBTS",_net_weight="367121603.1379 BEOS",_cpu_weight="367121603.1380 BEOS",_ram_bytes=10664105448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		node.wait_till_block(12)
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
		summary.action_status(node.issue(_to=accounts[1].name,_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
		node.wait_till_block(20)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="10.0000 PXBTS",_net_weight="611869338.5632 BEOS",_cpu_weight="611869338.5633 BEOS",_ram_bytes=24882905448))
		node.wait_till_block(21)
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="5.0000 PXBTS",_net_weight="122373867.7126 BEOS",_cpu_weight="122373867.7127 BEOS",_ram_bytes=7109405448))
		node.wait_till_block(22)
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
		summary.action_status(node.issue(_to=accounts[1].name,_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
		node.wait_till_block(30)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="15.0000 PXBTS",_net_weight="832142300.4459 BEOS",_cpu_weight="832142300.4461 BEOS",_ram_bytes=24882905448))
		node.wait_till_block(31)
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="10.0000 PXBTS",_net_weight="269222508.9677 BEOS",_cpu_weight="269222508.9679 BEOS",_ram_bytes=7109405448))
		node.wait_till_block(32)
		summary.action_status(node.issue(_to=accounts[0].name,_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
		summary.action_status(node.issue(_to=accounts[1].name,_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
		node.wait_till_block(40)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="20.0000 PXBTS",_net_weight="1041926073.6676 BEOS",_cpu_weight="1041926073.6678 BEOS",_ram_bytes=24882905448))
		node.wait_till_block(41)
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="15.0000 PXBTS",_net_weight="426560338.8839 BEOS",_cpu_weight="426560338.8842 BEOS",_ram_bytes=7109405448))
		node.wait_till_block(51)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="20.0000 PXBTS",_net_weight="1251709846.8893 BEOS",_cpu_weight="1251709846.8895 BEOS",_ram_bytes=24882905448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="15.0000 PXBTS",_net_weight="583898168.8002 BEOS",_cpu_weight="583898168.8005 BEOS",_ram_bytes=7109405448))
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="20.0000 PXBTS",_net_weight="1251709846.8893 BEOS",_cpu_weight="1251709846.8895 BEOS",_ram_bytes=24882905448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="15.0000 PXBTS",_net_weight="583898168.8002 BEOS",_cpu_weight="583898168.8005 BEOS",_ram_bytes=7109405448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)