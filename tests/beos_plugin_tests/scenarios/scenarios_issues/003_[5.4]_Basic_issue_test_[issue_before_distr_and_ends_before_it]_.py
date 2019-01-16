#!/usr/bin/python3

# Scenario based on test : [5.4]-Basic-issue-test-[issue-before-distr-and-ends-before-it]

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

	node.run_node(currentdir+r"/node/[5.4]-Basic-issue-test-[issue-before-distr-and-ends-before-it]/", currentdir+r"/logs/[5.4]-Basic-issue-test-[issue-before-distr-and-ends-before-it]/")
	summary = Summarizer(currentdir+r"/[5.4]-Basic-issue-test-[issue-before-distr-and-ends-before-it]")

	add_handler(currentdir+r"/logs/[5.4]-Basic-issue-test-[issue-before-distr-and-ends-before-it]/[5.4]-Basic-issue-test-[issue-before-distr-and-ends-before-it]")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 410, [1000,0,1001,10,8000000], [1000,0,1001,4,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abr") )
	summary.action_status(node.create_account("beos.tst.aby") )
	summary.action_status(node.issue(_to="beos.tst.abr",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.aby",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abr", ResourceResult(_balance="20.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.user_block_status(node, "beos.tst.aby", ResourceResult(_balance="20.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)