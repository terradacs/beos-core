#!/usr/bin/python3

# Scenario based on test : [5.6]-Withdraw-of-PXBTS-attempt-with-BEOS-inside-distribution-period

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

	node.run_node(currentdir+r"/node/[5.6]-Withdraw-of-PXBTS-attempt-with-BEOS-inside-distribution-period/", currentdir+r"/logs/[5.6]-Withdraw-of-PXBTS-attempt-with-BEOS-inside-distribution-period/")
	summary = Summarizer(currentdir+r"/[5.6]-Withdraw-of-PXBTS-attempt-with-BEOS-inside-distribution-period")

	add_handler(currentdir+r"/logs/[5.6]-Withdraw-of-PXBTS-attempt-with-BEOS-inside-distribution-period/[5.6]-Withdraw-of-PXBTS-attempt-with-BEOS-inside-distribution-period")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 20, [20,0,100,20,8000000], [20,0,100,20,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abs") )
	summary.action_status(node.create_account("beos.tst.abz") )
	summary.action_status(node.create_account("beos.tst.acc") )
	summary.action_status(node.create_account("beos.tst.ace") )
	summary.action_status(node.issue(_to="beos.tst.abs",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.abz",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.acc",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.ace",_quantity="20.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(30)
	summary.action_status(node.withdraw(_from="beos.tst.abs",_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="") )
	summary.user_block_status(node, "beos.tst.abs", ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
	summary.user_block_status(node, "beos.tst.abz", ResourceResult(_balance="20.0000 PXBTS",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
	summary.user_block_status(node, "beos.tst.acc", ResourceResult(_balance="20.0000 PXBTS",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
	summary.user_block_status(node, "beos.tst.ace", ResourceResult(_balance="20.0000 PXBTS",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
	node.wait_till_block(50)
	summary.action_status(node.withdraw(_from="beos.tst.abz",_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="") )
	summary.user_block_status(node, "beos.tst.abs", ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
	summary.user_block_status(node, "beos.tst.abz", ResourceResult(_balance="",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
	summary.user_block_status(node, "beos.tst.ace", ResourceResult(_balance="20.0000 PXBTS",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
	node.wait_till_block(56)
	summary.user_block_status(node, "beos.tst.acc", ResourceResult(_balance="20.0000 PXBTS",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
	node.wait_till_block(70)
	summary.action_status(node.withdraw(_from="beos.tst.acc",_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="") )
	node.wait_till_block(74)
	summary.user_block_status(node, "beos.tst.abs", ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
	summary.user_block_status(node, "beos.tst.abz", ResourceResult(_balance="",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
	summary.user_block_status(node, "beos.tst.acc", ResourceResult(_balance="",_net_weight="397715070.0660 BEOS",_cpu_weight="397715070.0662 BEOS",_ram_bytes=6931670448))
	summary.user_block_status(node, "beos.tst.ace", ResourceResult(_balance="20.0000 PXBTS",_net_weight="397715070.0660 BEOS",_cpu_weight="397715070.0662 BEOS",_ram_bytes=6931670448))
	node.wait_till_block(82)
	summary.user_block_status(node, "beos.tst.abz", ResourceResult(_balance="",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
	summary.action_status(node.withdraw(_from="beos.tst.ace",_bts_to="any_account",_quantity="20.0000 PXBTS",_memo="") )
	summary.user_block_status(node, "beos.tst.acc", ResourceResult(_balance="",_net_weight="397715070.0660 BEOS",_cpu_weight="397715070.0662 BEOS",_ram_bytes=6931670448))
	summary.user_block_status(node, "beos.tst.abs", ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
	summary.user_block_status(node, "beos.tst.ace", ResourceResult(_balance="",_net_weight="764836673.2040 BEOS",_cpu_weight="764836673.2042 BEOS",_ram_bytes=13330130448))
	
	#At end
	summary.user_block_status(node, "beos.tst.abs", ResourceResult(_balance="",_net_weight="91780400.7844 BEOS",_cpu_weight="91780400.7845 BEOS",_ram_bytes=1599620448))
	summary.user_block_status(node, "beos.tst.abz", ResourceResult(_balance="",_net_weight="214154268.4970 BEOS",_cpu_weight="214154268.4972 BEOS",_ram_bytes=3732440448))
	summary.user_block_status(node, "beos.tst.acc", ResourceResult(_balance="",_net_weight="397715070.0660 BEOS",_cpu_weight="397715070.0662 BEOS",_ram_bytes=6931670448))
	summary.user_block_status(node, "beos.tst.ace", ResourceResult(_balance="",_net_weight="764836673.2040 BEOS",_cpu_weight="764836673.2042 BEOS",_ram_bytes=13330130448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)