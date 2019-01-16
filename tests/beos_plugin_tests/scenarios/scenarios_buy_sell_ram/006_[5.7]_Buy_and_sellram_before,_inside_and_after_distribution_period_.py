#!/usr/bin/python3

# Scenario based on test : [5.7]-Buy-and-sellram-before,-inside-and-after-distribution-period

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

	node.run_node(currentdir+r"/node/[5.7]-Buy-and-sellram-before,-inside-and-after-distribution-period/", currentdir+r"/logs/[5.7]-Buy-and-sellram-before,-inside-and-after-distribution-period/")
	summary = Summarizer(currentdir+r"/[5.7]-Buy-and-sellram-before,-inside-and-after-distribution-period")

	add_handler(currentdir+r"/logs/[5.7]-Buy-and-sellram-before,-inside-and-after-distribution-period/[5.7]-Buy-and-sellram-before,-inside-and-after-distribution-period")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 420, [10,0,30,10,8000000], [10,0,30,10,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abt") )
	summary.action_status(node.create_account("beos.tst.aca") )
	summary.action_status(node.issue(_to="beos.tst.abt",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.aca",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.sellram(_account="beos.tst.abt",_bytes="10000"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
	summary.action_status(node.buyram(_payer="beos.tst.abt",_receiver="beos.tst.aca",_quant="1.0000 BEOS"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
	node.wait_till_block(20)
	summary.action_status(node.sellram(_account="beos.tst.abt",_bytes="10000"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
	node.wait_till_block(20)
	summary.action_status(node.buyram(_payer="beos.tst.abt",_receiver="beos.tst.aca",_quant="1.0000 BEOS"), ActionResult(False, "RAM shouldn't be liquid during distribution period") )
	node.wait_till_block(35)
	summary.action_status(node.sellram(_account="beos.tst.abt",_bytes="10000") )
	summary.action_status(node.buyram(_payer="beos.tst.abt",_receiver="beos.tst.aca",_quant="10.0000 BEOS"), ActionResult(False, "overdrawn balance") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abt", ResourceResult(_balance="20.0000 PXBTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996145448))
	summary.user_block_status(node, "beos.tst.aca", ResourceResult(_balance="20.0000 PXBTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)