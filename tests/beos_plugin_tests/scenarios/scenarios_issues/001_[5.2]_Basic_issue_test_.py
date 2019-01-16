#!/usr/bin/python3

# Scenario based on test : [5.2]-Basic-issue-test

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

	node.run_node(currentdir+r"/node/[5.2]-Basic-issue-test/", currentdir+r"/logs/[5.2]-Basic-issue-test/")
	summary = Summarizer(currentdir+r"/[5.2]-Basic-issue-test")

	add_handler(currentdir+r"/logs/[5.2]-Basic-issue-test/[5.2]-Basic-issue-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 120, [10,0,30,5,1000000], [10,0,20,5,0], 300000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aal") )
	summary.action_status(node.issue(_to="beos.tst.aal",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.user_block_status(node, "beos.tst.aal", ResourceResult(_balance="5.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	node.wait_till_block(10)
	summary.action_status(node.issue(_to="beos.tst.aal",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(12)
	summary.user_block_status(node, "beos.tst.aal", ResourceResult(_balance="10.0000 PXBTS",_net_weight="367121673.1379 BEOS",_cpu_weight="367121673.1380 BEOS",_ram_bytes=10666672114))
	node.wait_till_block(15)
	summary.action_status(node.issue(_to="beos.tst.aal",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(17)
	summary.user_block_status(node, "beos.tst.aal", ResourceResult(_balance="15.0000 PXBTS",_net_weight="734243346.2758 BEOS",_cpu_weight="734243346.2760 BEOS",_ram_bytes=21333338781))
	node.wait_till_block(20)
	summary.action_status(node.issue(_to="beos.tst.aal",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(22)
	summary.user_block_status(node, "beos.tst.aal", ResourceResult(_balance="20.0000 PXBTS",_net_weight="1101365019.4137 BEOS",_cpu_weight="1101365019.4140 BEOS",_ram_bytes=32000005448))
	
	#At end
	summary.user_block_status(node, "beos.tst.aal", ResourceResult(_balance="20.0000 PXBTS",_net_weight="1101365019.4137 BEOS",_cpu_weight="1101365019.4140 BEOS",_ram_bytes=32000005448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)