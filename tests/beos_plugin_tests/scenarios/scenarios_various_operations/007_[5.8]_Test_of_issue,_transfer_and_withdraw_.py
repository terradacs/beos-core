#!/usr/bin/python3

# Scenario based on test : [5.8]-Test-of-issue,-transfer-and-withdraw

import os
import sys
import time
import datetime 

if __name__ == "__main__":
	currentdir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
	from beos_test_utils.logger        import add_handler
	from beos_test_utils.beosnode      import BEOSNode
	from beos_test_utils.summarizer    import *
	from beos_test_utils.cmdlineparser import parser
	args = parser.parse_args()
	node = BEOSNode(args.nodeos_ip, args.nodeos_port, args.keosd_ip,
		args.keosd_port, args.master_wallet_name, args.path_to_cleos, args.path_to_keosd, int(args.scenario_multiplier))

	node.run_node(currentdir+r"/node/[5.8]-Test-of-issue,-transfer-and-withdraw/", currentdir+r"/logs/[5.8]-Test-of-issue,-transfer-and-withdraw/")
	summary = Summarizer(currentdir+r"/[5.8]-Test-of-issue,-transfer-and-withdraw")

	add_handler(currentdir+r"/logs/[5.8]-Test-of-issue,-transfer-and-withdraw/[5.8]-Test-of-issue,-transfer-and-withdraw")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 190, [55,0,60,5,8000000], [55,0,60,5,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.acf") )
	summary.action_status(node.create_account("beos.tst.aab") )
	summary.action_status(node.issue(_to="beos.tst.acf",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.aab",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.transfer(_from="beos.tst.acf",_to="beos.tst.aab",_quantity="20.0000 PXBTS",_memo=" internal transfer 0"), ActionResult(False, "transaction net usage is too high") )
	node.wait_till_block(55)
	summary.action_status(node.transfer(_from="beos.tst.acf",_to="beos.tst.aab",_quantity="20.0000 PXBTS",_memo=" internal transfer 1") )
	node.wait_till_block(62)
	summary.action_status(node.transfer(_from="beos.tst.aab",_to="beos.tst.acf",_quantity="20.0000 PXBTS",_memo=" internal transfer 2") )
	summary.action_status(node.withdraw(_from="beos.tst.acf",_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="") )
	summary.action_status(node.withdraw(_from="beos.tst.aab",_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="") )
	summary.action_status(node.transfer(_from="beos.tst.acf",_to="beos.tst.aab",_quantity="20.0000 PXBTS",_memo=" internal transfer 3"), ActionResult(False, "no balance object found") )
	
	#At end
	summary.user_block_status(node, "beos.tst.acf", ResourceResult(_balance="",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=7998080448))
	summary.user_block_status(node, "beos.tst.aab", ResourceResult(_balance="",_net_weight="1376706011.7673 BEOS",_cpu_weight="1376706011.7674 BEOS",_ram_bytes=23994230448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)