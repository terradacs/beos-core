#!/usr/bin/python3

# Scenario based on test : [5.1]-Basic-issue-test

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
		accounts = node.create_accounts(1, "5.0000 BTS")
		tester = accounts[0].name

		node.run_node()
		#Changeparams
		newparams = {
			"beos" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 30,
				"block_interval" : 5, 
				"trustee_reward" : 1000000
			},
			"ram" : {
				"starting_block" : 10,
				"next_block" : 0, 
				"ending_block" : 18,
				"block_interval" : 4, 
				"trustee_reward" : 0 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 300000,
			"starting_block_for_initial_witness_election":10
		}

		node.changeparams(newparams)

		#Changes in _ram_bytes values [AD 1] due to this commit: 93430498700a04b8bb49612ebbddffcc144e627c, from 12 Jul, 2019
		
		#Actions
		summary.user_block_status(node, tester, ResourceResult(_balance="5.0000 BTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
		node.wait_till_block(11)
		#[AD 1] Previous _ram_bytes = 10666672114
		summary.user_block_status(node, tester, ResourceResult(_balance="5.0000 BTS",_net_weight="367121673.1379 BEOS",_cpu_weight="367121673.1380 BEOS",_ram_bytes=10666672052))
		node.wait_till_block(16)
		#[AD 1] Previous _ram_bytes = 21333338781
		summary.user_block_status(node, tester, ResourceResult(_balance="5.0000 BTS",_net_weight="734243346.2758 BEOS",_cpu_weight="734243346.2760 BEOS",_ram_bytes=21333338656))
		node.wait_till_block(21)
		#[AD 1] Previous _ram_bytes = 32000005448
		summary.user_block_status(node, tester, ResourceResult(_balance="5.0000 BTS",_net_weight="1101365019.4137 BEOS",_cpu_weight="1101365019.4140 BEOS",_ram_bytes=32000005261))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)
