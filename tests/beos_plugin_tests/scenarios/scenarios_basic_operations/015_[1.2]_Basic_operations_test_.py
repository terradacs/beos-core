#!/usr/bin/python3

# Scenario based on test : [1.2]-Basic-operations-test

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

	node.run_node(currentdir+r"/node/[1.2]-Basic-operations-test/", currentdir+r"/logs/[1.2]-Basic-operations-test/")
	summary = Summarizer(currentdir+r"/[1.2]-Basic-operations-test")

	add_handler(currentdir+r"/logs/[1.2]-Basic-operations-test/[1.2]-Basic-operations-test")
	node.wait_n_blocks(2)
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 140, [20,0,25,10,1000000], [20,0,25,10,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aar") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aar",_quantity="5.0000 PXBTS",_memo="") )
	node.wait_till_block(20)
	summary.user_block_status(node, "beos.tst.aar", ResourceResult(_balance="5.0000 PXBTS",_net_weight="1835608365.6898 BEOS",_cpu_weight="1835608365.6898 BEOS",_ram_bytes=31992305448))
	node.wait_till_block(25)
	summary.user_block_status(node, "beos.tst.aar", ResourceResult(_balance="5.0000 PXBTS",_net_weight="1835608365.6898 BEOS",_cpu_weight="1835608365.6898 BEOS",_ram_bytes=31992305448))
	node.wait_till_block(30)
	summary.user_block_status(node, "beos.tst.aar", ResourceResult(_balance="5.0000 PXBTS",_net_weight="1835608365.6898 BEOS",_cpu_weight="1835608365.6898 BEOS",_ram_bytes=31992305448))
	summary.action_status(node.withdraw(_from="beos.tst.aar",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aar", ResourceResult(_balance="",_net_weight="1835608365.6898 BEOS",_cpu_weight="1835608365.6898 BEOS",_ram_bytes=31992305448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)