#!/usr/bin/python3

# Scenario based on test : [5.1]-Basic-issue-test

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

	node.run_node(currentdir+r"/node/[5.1]-Basic-issue-test/", currentdir+r"/logs/[5.1]-Basic-issue-test/")
	summary = Summarizer(currentdir+r"/[5.1]-Basic-issue-test")

	add_handler(currentdir+r"/logs/[5.1]-Basic-issue-test/[5.1]-Basic-issue-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 10, [10,0,30,5,1000000], [10,0,18,4,0], 300000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aaa") )
	summary.action_status(node.issue(_to="beos.tst.aaa",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(8)
	summary.user_block_status(node, "beos.tst.aaa", ResourceResult(_balance="5.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	node.wait_till_block(11)
	summary.user_block_status(node, "beos.tst.aaa", ResourceResult(_balance="5.0000 PXBTS",_net_weight="367121673.1379 BEOS",_cpu_weight="367121673.1380 BEOS",_ram_bytes=10666672114))
	node.wait_till_block(16)
	summary.user_block_status(node, "beos.tst.aaa", ResourceResult(_balance="5.0000 PXBTS",_net_weight="734243346.2758 BEOS",_cpu_weight="734243346.2760 BEOS",_ram_bytes=21333338781))
	node.wait_till_block(21)
	summary.user_block_status(node, "beos.tst.aaa", ResourceResult(_balance="5.0000 PXBTS",_net_weight="1101365019.4137 BEOS",_cpu_weight="1101365019.4140 BEOS",_ram_bytes=32000005448))
	
	#At end
	summary.user_block_status(node, "beos.tst.aaa", ResourceResult(_balance="5.0000 PXBTS",_net_weight="1101365019.4137 BEOS",_cpu_weight="1101365019.4140 BEOS",_ram_bytes=32000005448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)
