#!/usr/bin/python3

# Scenario based on test : [2.7]-Buy-and-sell-ram-tests

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

	node.run_node(currentdir+r"/node/[2.7]-Buy-and-sell-ram-tests/", currentdir+r"/logs/[2.7]-Buy-and-sell-ram-tests/")
	summary = Summarizer(currentdir+r"/[2.7]-Buy-and-sell-ram-tests")

	add_handler(currentdir+r"/logs/[2.7]-Buy-and-sell-ram-tests/[2.7]-Buy-and-sell-ram-tests")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 10, [10,0,11,5,2000000], [15,0,25,5,1000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abn") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.abn",_quantity="10.0000 PXBTS",_memo="") )
	node.wait_till_block(10)
	summary.action_status(node.sellram(_account="beos.tst.abn",_bytes="1000000"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
	node.wait_till_block(20)
	summary.action_status(node.sellram(_account="beos.tst.abn",_bytes="1000000"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
	node.wait_till_block(27)
	summary.user_block_status(node, "beos.tst.abn", ResourceResult(_balance="10.0000 PXBTS",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
	summary.action_status(node.sellram(_account="beos.tst.abn",_bytes="2000000") )
	summary.action_status(node.buyrambytes(_payer="beos.tst.abn",_receiver="beos.tst.abn",_bytes="8000000"), ActionResult(False, "overdrawn balance") )
	summary.action_status(node.sellram(_account="beos.tst.abn",_bytes="100000000") )
	summary.action_status(node.buyrambytes(_payer="beos.tst.abn",_receiver="beos.tst.abn",_bytes="1000000") )
	summary.action_status(node.buyrambytes(_payer="beos.tst.abn",_receiver="beos.tst.abn",_bytes="2000000") )
	summary.action_status(node.withdraw(_from="beos.tst.abn",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abn", ResourceResult(_balance="",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31897305448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)