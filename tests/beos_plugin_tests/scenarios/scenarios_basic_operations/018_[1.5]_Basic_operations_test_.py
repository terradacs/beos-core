#!/usr/bin/python3

# Scenario based on test : [1.5]-Basic-operations-test

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

	node.run_node(currentdir+r"/node/[1.5]-Basic-operations-test/", currentdir+r"/logs/[1.5]-Basic-operations-test/")
	summary = Summarizer(currentdir+r"/[1.5]-Basic-operations-test")

	add_handler(currentdir+r"/logs/[1.5]-Basic-operations-test/[1.5]-Basic-operations-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 10, [17,0,21,5,8000000], [15,0,18,5,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aax") )
	summary.action_status(node.create_account("beos.tst.aay") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aax",_quantity="0.00001 PXBTS",_memo=""), ActionResult(False, "symbol precision mismatch") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aax",_quantity="0.0001 PXBTS",_memo="") )
	node.wait_till_block(22)
	summary.user_block_status(node, "beos.tst.aax", ResourceResult(_balance="0.0001 PXBTS",_net_weight="1835608015.6898 BEOS",_cpu_weight="1835608015.6898 BEOS",_ram_bytes=31992305448))
	node.wait_till_block(25)
	summary.action_status(node.transfer(_from="beos.tst.aax",_to="beos.tst.aay",_quantity="0.00001 PXBTS",_memo=""), ActionResult(False, "symbol precision mismatch") )
	summary.action_status(node.transfer(_from="beos.tst.aax",_to="beos.tst.aay",_quantity="-0.00001 PXBTS",_memo=""), ActionResult(False, "must transfer positive quantity") )
	summary.action_status(node.transfer(_from="beos.tst.aax",_to="beos.tst.aay",_quantity="-0.00001 PXBTS",_memo=""), ActionResult(False, "must transfer positive quantity") )
	summary.action_status(node.withdraw(_from="beos.tst.aax",_bts_to="any_account",_quantity="0.0001 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aax", ResourceResult(_balance="",_net_weight="1835608015.6898 BEOS",_cpu_weight="1835608015.6898 BEOS",_ram_bytes=31992305448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)