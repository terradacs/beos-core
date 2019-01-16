#!/usr/bin/python3

# Scenario based on test : [5.3]-Basic-issue-test

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

	node.run_node(currentdir+r"/node/[5.3]-Basic-issue-test/", currentdir+r"/logs/[5.3]-Basic-issue-test/")
	summary = Summarizer(currentdir+r"/[5.3]-Basic-issue-test")

	add_handler(currentdir+r"/logs/[5.3]-Basic-issue-test/[5.3]-Basic-issue-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 140, [10,0,50,10,8000000], [10,0,20,5,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aaw") )
	summary.action_status(node.create_account("beos.tst.abg") )
	summary.action_status(node.issue(_to="beos.tst.aaw",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(11)
	summary.user_block_status(node, "beos.tst.aaw", ResourceResult(_balance="5.0000 PXBTS",_net_weight="367121603.1379 BEOS",_cpu_weight="367121603.1380 BEOS",_ram_bytes=10664105448))
	summary.user_block_status(node, "beos.tst.abg", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	node.wait_till_block(12)
	summary.action_status(node.issue(_to="beos.tst.aaw",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.abg",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(20)
	summary.user_block_status(node, "beos.tst.aaw", ResourceResult(_balance="10.0000 PXBTS",_net_weight="611869338.5632 BEOS",_cpu_weight="611869338.5633 BEOS",_ram_bytes=24882905448))
	node.wait_till_block(21)
	summary.user_block_status(node, "beos.tst.abg", ResourceResult(_balance="5.0000 PXBTS",_net_weight="122373867.7126 BEOS",_cpu_weight="122373867.7127 BEOS",_ram_bytes=7109405448))
	node.wait_till_block(22)
	summary.action_status(node.issue(_to="beos.tst.aaw",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.abg",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(30)
	summary.user_block_status(node, "beos.tst.aaw", ResourceResult(_balance="15.0000 PXBTS",_net_weight="832142300.4459 BEOS",_cpu_weight="832142300.4461 BEOS",_ram_bytes=24882905448))
	node.wait_till_block(31)
	summary.user_block_status(node, "beos.tst.abg", ResourceResult(_balance="10.0000 PXBTS",_net_weight="269222508.9677 BEOS",_cpu_weight="269222508.9679 BEOS",_ram_bytes=7109405448))
	node.wait_till_block(32)
	summary.action_status(node.issue(_to="beos.tst.aaw",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.abg",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(40)
	summary.user_block_status(node, "beos.tst.aaw", ResourceResult(_balance="20.0000 PXBTS",_net_weight="1041926073.6676 BEOS",_cpu_weight="1041926073.6678 BEOS",_ram_bytes=24882905448))
	node.wait_till_block(41)
	summary.user_block_status(node, "beos.tst.abg", ResourceResult(_balance="15.0000 PXBTS",_net_weight="426560338.8839 BEOS",_cpu_weight="426560338.8842 BEOS",_ram_bytes=7109405448))
	node.wait_till_block(51)
	summary.user_block_status(node, "beos.tst.aaw", ResourceResult(_balance="20.0000 PXBTS",_net_weight="1251709846.8893 BEOS",_cpu_weight="1251709846.8895 BEOS",_ram_bytes=24882905448))
	summary.user_block_status(node, "beos.tst.abg", ResourceResult(_balance="15.0000 PXBTS",_net_weight="583898168.8002 BEOS",_cpu_weight="583898168.8005 BEOS",_ram_bytes=7109405448))
	
	#At end
	summary.user_block_status(node, "beos.tst.aaw", ResourceResult(_balance="20.0000 PXBTS",_net_weight="1251709846.8893 BEOS",_cpu_weight="1251709846.8895 BEOS",_ram_bytes=24882905448))
	summary.user_block_status(node, "beos.tst.abg", ResourceResult(_balance="15.0000 PXBTS",_net_weight="583898168.8002 BEOS",_cpu_weight="583898168.8005 BEOS",_ram_bytes=7109405448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)