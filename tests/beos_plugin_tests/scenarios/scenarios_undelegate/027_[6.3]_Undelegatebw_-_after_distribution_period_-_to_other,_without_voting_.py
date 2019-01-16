#!/usr/bin/python3

# Scenario based on test : [6.3]-Undelegatebw---after-distribution-period---to-other,-without-voting

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

	node.run_node(currentdir+r"/node/[6.3]-Undelegatebw---after-distribution-period---to-other,-without-voting/", currentdir+r"/logs/[6.3]-Undelegatebw---after-distribution-period---to-other,-without-voting/")
	summary = Summarizer(currentdir+r"/[6.3]-Undelegatebw---after-distribution-period---to-other,-without-voting")

	add_handler(currentdir+r"/logs/[6.3]-Undelegatebw---after-distribution-period---to-other,-without-voting/[6.3]-Undelegatebw---after-distribution-period---to-other,-without-voting")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 1, [10,0,30,5,8000000], [10,0,20,5,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abs") )
	summary.action_status(node.create_account("beos.tst.abq") )
	summary.action_status(node.issue(_to="beos.tst.abs",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.abq",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(35)
	summary.action_status(node.undelegatebw(_from="beos.tst.abs",_receiver="beos.tst.abq",_unstake_net_quantity="1.0000 BEOS",_unstake_cpu_quantity="1.0000 BEOS"), ActionResult(False, "") )
	summary.action_status(node.withdraw(_from="beos.tst.abq",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.withdraw(_from="beos.tst.abs",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abs", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.user_block_status(node, "beos.tst.abq", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)