#!/usr/bin/python3

# Scenario based on test : [2.2]-Basic-operations-test

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

	node.run_node(currentdir+r"/node/[2.2]-Basic-operations-test/", currentdir+r"/logs/[2.2]-Basic-operations-test/")
	summary = Summarizer(currentdir+r"/[2.2]-Basic-operations-test")

	add_handler(currentdir+r"/logs/[2.2]-Basic-operations-test/[2.2]-Basic-operations-test")
	node.wait_n_blocks(2)
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 40, [25,0,30,5,2000000], [25,0,30,5,1000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aae") )
	summary.action_status(node.withdraw(_from="beos.tst.aae",_bts_to="any_account",_quantity="1.0000 PXBTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aae",_quantity="10.0000 PXBTS",_memo="") )
	summary.action_status(node.withdraw(_from="beos.tst.aae",_bts_to="any_account",_quantity="1.0000 PXBTS",_memo="_memo"), ActionResult(False, "transaction net usage is too high: 128 > 0") )
	summary.user_block_status(node, "beos.tst.aae", ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	node.wait_till_block(35)
	summary.user_block_status(node, "beos.tst.aae", ResourceResult(_balance="10.0000 PXBTS",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
	summary.action_status(node.withdraw(_from="beos.tst.aae",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	summary.action_status(node.withdraw(_from="beos.tst.aae",_bts_to="any_account",_quantity="1.0000 PXBTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aae", ResourceResult(_balance="",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)