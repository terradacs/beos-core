#!/usr/bin/python3

# Scenario based on test : [1.8]-Withdraw-done-by-other-normal-user

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

	node.run_node(currentdir+r"/node/[1.8]-Withdraw-done-by-other-normal-user/", currentdir+r"/logs/[1.8]-Withdraw-done-by-other-normal-user/")
	summary = Summarizer(currentdir+r"/[1.8]-Withdraw-done-by-other-normal-user")

	add_handler(currentdir+r"/logs/[1.8]-Withdraw-done-by-other-normal-user/[1.8]-Withdraw-done-by-other-normal-user")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 10, [25,0,34,5,8000000], [25,0,34,5,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abi") )
	summary.action_status(node.create_account("beos.tst.abj") )
	key = node.utils.create_key()
	summary.action_status(node.create_account("beos.tst.abk",_activ_key=key, _owner_key=key) )
	summary.action_status(node.issue(_to="beos.tst.abi",_quantity="10.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.abk",_quantity="10.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.user_block_status(node, "beos.tst.abi", ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.user_block_status(node, "beos.tst.abj", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.user_block_status(node, "beos.tst.abk", ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.action_status(node.withdraw(_from="beos.tst.abi",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo=""), ActionResult(False, "transaction net usage is too high: 128 > 0") )
	summary.user_block_status(node, "beos.tst.abi", ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.action_status(node.withdraw(_from="beos.tst.abj",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="", _authorized_by="beos.tst.abi"), ActionResult(False, "missing authority of beos.tst.abj") )
	summary.user_block_status(node, "beos.tst.abj", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.action_status(node.withdraw(_from="beos.tst.abi",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="", _authorized_by="beos.tst.abj"), ActionResult(False, "missing authority of beos.tst.abi") )
	summary.user_block_status(node, "beos.tst.abi", ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.action_status(node.withdraw(_from="beos.tst.abj",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo=""), ActionResult(False, "overdrawn balance during withdraw") )
	node.wait_till_block(28)
	summary.user_block_status(node, "beos.tst.abj", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	node.wait_till_block(38)
	summary.action_status(node.regproducer(_producer="beos.tst.abk",_producer_key=key,_url="test.html",_location=0) )
	summary.action_status(node.withdraw(_from="beos.tst.abj",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="", _authorized_by="beos.tst.abi"), ActionResult(False, "missing authority of beos.tst.abj") )
	summary.user_block_status(node, "beos.tst.abj", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.action_status(node.withdraw(_from="beos.tst.abi",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="", _authorized_by="beos.tst.abj"), ActionResult(False, "missing authority of beos.tst.abi") )
	summary.user_block_status(node, "beos.tst.abi", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.action_status(node.withdraw(_from="beos.tst.abi",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="", _authorized_by="beos.tst.abj"), ActionResult(False, "missing authority of beos.tst.abi") )
	summary.user_block_status(node, "beos.tst.abi", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.action_status(node.withdraw(_from="beos.tst.abj",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="", _authorized_by="beos.tst.abi"), ActionResult(False, "missing authority of beos.tst.abj") )
	summary.user_block_status(node, "beos.tst.abj", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.action_status(node.withdraw(_from="beos.tst.abk",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="", _authorized_by="beos.tst.abi"), ActionResult(False, "missing authority of beos.tst.abk") )
	summary.user_block_status(node, "beos.tst.abk", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.action_status(node.withdraw(_from="beos.tst.abk",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="", _authorized_by="beos.tst.abi"), ActionResult(False, "missing authority of beos.tst.abk") )
	summary.user_block_status(node, "beos.tst.abk", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.action_status(node.withdraw(_from="beos.tst.abi",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="") )
	summary.action_status(node.withdraw(_from="beos.tst.abk",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abi", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.user_block_status(node, "beos.tst.abj", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.user_block_status(node, "beos.tst.abk", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)