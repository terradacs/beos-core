#!/usr/bin/python3

# Scenario based on test : [2.1]-Basic-operations-test

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

	node.run_node(currentdir+r"/node/[2.1]-Basic-operations-test/", currentdir+r"/logs/[2.1]-Basic-operations-test/")
	summary = Summarizer(currentdir+r"/[2.1]-Basic-operations-test")

	add_handler(currentdir+r"/logs/[2.1]-Basic-operations-test/[2.1]-Basic-operations-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 40, [20,0,40,20,4000000], [20,0,40,20,2000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aac") )
	summary.action_status(node.create_account("beos.tst.aad") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aac",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aad",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.withdraw(_from="beos.tst.aac",_bts_to="any_account",_quantity="1.0000 PXBTS",_memo="_memo"), ActionResult(False, "transaction net usage is too high: 128 > 0") )
	summary.user_block_status(node, "beos.tst.aac", ResourceResult(_balance="5.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.user_block_status(node, "beos.tst.aad", ResourceResult(_balance="5.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	node.wait_till_block(30)
	summary.action_status(node.withdraw(_from="beos.tst.aac",_bts_to="any_account",_quantity="1.0000 PXBTS",_memo="_memo") )
	node.wait_till_block(30)
	summary.action_status(node.withdraw(_from="beos.tst.aad",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="_memo") )
	node.wait_till_block(35)
	summary.user_block_status(node, "beos.tst.aac", ResourceResult(_balance="4.0000 PXBTS",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
	node.wait_till_block(35)
	summary.user_block_status(node, "beos.tst.aad", ResourceResult(_balance="",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
	node.wait_till_block(45)
	summary.user_block_status(node, "beos.tst.aac", ResourceResult(_balance="4.0000 PXBTS",_net_weight="1376706161.7673 BEOS",_cpu_weight="1376706161.7674 BEOS",_ram_bytes=23996480448))
	summary.user_block_status(node, "beos.tst.aad", ResourceResult(_balance="",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aad",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.withdraw(_from="beos.tst.aad",_bts_to="any_account",_quantity="1.0000 PXBTS",_memo="_memo") )
	summary.action_status(node.withdraw(_from="beos.tst.aad",_bts_to="any_account",_quantity="40.0000 PXBTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
	summary.action_status(node.transfer(_from="beos.tst.aad",_to="beos.tst.aac",_quantity="4.0000 PXBTS",_memo="any_memo") )
	summary.user_block_status(node, "beos.tst.aac", ResourceResult(_balance="8.0000 PXBTS",_net_weight="1376706161.7673 BEOS",_cpu_weight="1376706161.7674 BEOS",_ram_bytes=23996480448))
	summary.user_block_status(node, "beos.tst.aad", ResourceResult(_balance="",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
	summary.action_status(node.withdraw(_from="beos.tst.aad",_bts_to="any_account",_quantity="1.0000 PXBTS",_memo="_memo"), ActionResult(False, "overdrawn balance during withdraw") )
	summary.action_status(node.withdraw(_from="beos.tst.aac",_bts_to="any_account",_quantity="2.0000 PXBTS",_memo="_memo") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aad",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.withdraw(_from="beos.tst.aad",_bts_to="any_account",_quantity="1.0000 PXBTS",_memo="_memo") )
	summary.action_status(node.withdraw(_from="beos.tst.aac",_bts_to="any_account",_quantity="6.0000 PXBTS",_memo="_memo") )
	summary.action_status(node.withdraw(_from="beos.tst.aad",_bts_to="any_account",_quantity="4.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aac", ResourceResult(_balance="",_net_weight="1376706161.7673 BEOS",_cpu_weight="1376706161.7674 BEOS",_ram_bytes=23996480448))
	summary.user_block_status(node, "beos.tst.aad", ResourceResult(_balance="",_net_weight="458902053.9224 BEOS",_cpu_weight="458902053.9225 BEOS",_ram_bytes=7998830448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)