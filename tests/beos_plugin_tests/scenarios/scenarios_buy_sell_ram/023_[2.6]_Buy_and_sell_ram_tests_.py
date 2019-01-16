#!/usr/bin/python3

# Scenario based on test : [2.6]-Buy-and-sell-ram-tests

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

	node.run_node(currentdir+r"/node/[2.6]-Buy-and-sell-ram-tests/", currentdir+r"/logs/[2.6]-Buy-and-sell-ram-tests/")
	summary = Summarizer(currentdir+r"/[2.6]-Buy-and-sell-ram-tests")

	add_handler(currentdir+r"/logs/[2.6]-Buy-and-sell-ram-tests/[2.6]-Buy-and-sell-ram-tests")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 10, [10,0,15,5,4000000], [10,0,15,5,2000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abl") )
	summary.action_status(node.create_account("beos.tst.abm") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.abl",_quantity="10.0000 PXBTS",_memo="") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.abm",_quantity="10.0000 PXBTS",_memo="") )
	node.wait_till_block(16)
	summary.user_block_status(node, "beos.tst.abl", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804107.8448 BEOS",_cpu_weight="917804107.8450 BEOS",_ram_bytes=15997655448))
	summary.user_block_status(node, "beos.tst.abm", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804107.8448 BEOS",_cpu_weight="917804107.8450 BEOS",_ram_bytes=15997655448))
	summary.action_status(node.sellram(_account="beos.tst.abl",_bytes="1000000") )
	summary.action_status(node.sellram(_account="beos.tst.abm",_bytes="3000000") )
	summary.action_status(node.buyram(_payer="beos.tst.abl",_receiver="beos.tst.abl",_quant="0.0100 BEOS") )
	summary.action_status(node.withdraw(_from="beos.tst.abl",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	summary.action_status(node.withdraw(_from="beos.tst.abm",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abl", ResourceResult(_balance="",_net_weight="917804107.8448 BEOS",_cpu_weight="917804107.8450 BEOS",_ram_bytes=15996655499))
	summary.user_block_status(node, "beos.tst.abm", ResourceResult(_balance="",_net_weight="917804107.8448 BEOS",_cpu_weight="917804107.8450 BEOS",_ram_bytes=15994655448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)