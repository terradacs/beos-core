#!/usr/bin/python3

# Scenario based on test : [5.6]-Withdraw-of-BTS-attempt-with-BEOS-inside-distribution-period

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
		accounts = node.create_accounts(4, "20.0000 BTS")
		node.run_node()	
		#Changeparams
		#node.changeparams(["0.0000 BTS"], 20, [20,0,100,20,8000000], [20,0,100,20,5000000], 3000000)
		newparams = {
			"beos" : {
				"starting_block" : 20,
				"next_block" : 0, 
				"ending_block" : 100,
				"block_interval" : 20, 
				"trustee_reward" : 8000000
			},
			"ram" : {
				"starting_block" : 20,
				"next_block" : 0, 
				"ending_block" : 100,
				"block_interval" : 20, 
				"trustee_reward" : 5000000 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":20
		}
		node.changeparams(newparams)
		
		#Actions
		node.wait_till_block(30)
		summary.action_status(node.withdraw(_from=accounts[0].name,_bts_to="any_account",_quantity="20.0000 BTS",_memo="") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="20.0000 BTS",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
		summary.user_block_status(node, accounts[2].name, ResourceResult(_balance="20.0000 BTS",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
		summary.user_block_status(node, accounts[3].name, ResourceResult(_balance="20.0000 BTS",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
		node.wait_till_block(50)
		summary.action_status(node.withdraw(_from=accounts[1].name,_bts_to="any_account",_quantity="20.0000 BTS",_memo="") )
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
		summary.user_block_status(node, accounts[3].name, ResourceResult(_balance="20.0000 BTS",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
		node.wait_till_block(56)
		summary.user_block_status(node, accounts[2].name, ResourceResult(_balance="20.0000 BTS",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
		node.wait_till_block(70)
		summary.action_status(node.withdraw(_from=accounts[2].name,_bts_to="any_account",_quantity="20.0000 BTS",_memo="") )
		node.wait_till_block(74)
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
		summary.user_block_status(node, accounts[2].name, ResourceResult(_balance="",_net_weight="397715070.0660 BEOS",_cpu_weight="397715070.0662 BEOS",_ram_bytes=6931670448))
		summary.user_block_status(node, accounts[3].name, ResourceResult(_balance="20.0000 BTS",_net_weight="397715070.0660 BEOS",_cpu_weight="397715070.0662 BEOS",_ram_bytes=6931670448))
		node.wait_till_block(82)
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
		summary.action_status(node.withdraw(_from=accounts[3].name,_bts_to="any_account",_quantity="20.0000 BTS",_memo="") )
		summary.user_block_status(node, accounts[2].name, ResourceResult(_balance="",_net_weight="397715070.0660 BEOS",_cpu_weight="397715070.0662 BEOS",_ram_bytes=6931670448))
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
		summary.user_block_status(node, accounts[3].name, ResourceResult(_balance="",_net_weight="764836673.2040 BEOS",_cpu_weight="764836673.2042 BEOS",_ram_bytes=13330130448))
		
		#At end
		summary.user_block_status(node, accounts[0].name, ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
		summary.user_block_status(node, accounts[1].name, ResourceResult(_balance="",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
		summary.user_block_status(node, accounts[2].name, ResourceResult(_balance="",_net_weight="397715070.0660 BEOS",_cpu_weight="397715070.0662 BEOS",_ram_bytes=6931670448))
		summary.user_block_status(node, accounts[3].name, ResourceResult(_balance="",_net_weight="764836673.2040 BEOS",_cpu_weight="764836673.2042 BEOS",_ram_bytes=13330130448))
	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)