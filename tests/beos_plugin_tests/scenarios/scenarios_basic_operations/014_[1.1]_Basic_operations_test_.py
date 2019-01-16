#!/usr/bin/python3

# Scenario based on test : [1.1]-Basic-operations-test

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

	node.run_node(currentdir+r"/node/[1.1]-Basic-operations-test/", currentdir+r"/logs/[1.1]-Basic-operations-test/")
	summary = Summarizer(currentdir+r"/[1.1]-Basic-operations-test")

	add_handler(currentdir+r"/logs/[1.1]-Basic-operations-test/[1.1]-Basic-operations-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 40, [20,0,40,20,8000000], [20,0,40,10,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aap") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aap",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.create_account("beos.tst.aaq") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aaq",_quantity="5.0000 PXBTS",_memo="") )
	summary.user_block_status(node, "beos.tst.aap", ResourceResult(_balance="5.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.user_block_status(node, "beos.tst.aaq", ResourceResult(_balance="5.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.action_status(node.transfer(_from="beos.tst.aap",_to="beos.tst.aaq",_quantity="1.0000 PXBTS",_memo=""), ActionResult(False, "transaction net usage is too high: 128 > 0") )
	node.wait_till_block(20)
	summary.action_status(node.transfer(_from="beos.tst.aap",_to="beos.tst.aaq",_quantity="5.0000 PXBTS",_memo="") )
	summary.user_block_status(node, "beos.tst.aap", ResourceResult(_balance="",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	summary.user_block_status(node, "beos.tst.aaq", ResourceResult(_balance="10.0000 PXBTS",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	node.wait_till_block(24)
	summary.user_block_status(node, "beos.tst.aaq", ResourceResult(_balance="10.0000 PXBTS",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	node.wait_till_block(26)
	summary.user_block_status(node, "beos.tst.aap", ResourceResult(_balance="",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	node.wait_till_block(28)
	summary.action_status(node.transfer(_from="beos.tst.aap",_to="beos.tst.aaq",_quantity="1.0000 PXBTS",_memo=""), ActionResult(False, "no balance object found") )
	summary.user_block_status(node, "beos.tst.aaq", ResourceResult(_balance="10.0000 PXBTS",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	node.wait_till_block(30)
	summary.user_block_status(node, "beos.tst.aap", ResourceResult(_balance="",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	node.wait_till_block(40)
	summary.user_block_status(node, "beos.tst.aap", ResourceResult(_balance="",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	summary.user_block_status(node, "beos.tst.aaq", ResourceResult(_balance="10.0000 PXBTS",_net_weight="1376706011.7673 BEOS",_cpu_weight="1376706011.7674 BEOS",_ram_bytes=26660255448))
	node.wait_till_block(50)
	summary.action_status(node.transfer(_from="beos.tst.aaq",_to="beos.tst.aap",_quantity="10.0000 PXBTS",_memo="") )
	summary.user_block_status(node, "beos.tst.aap", ResourceResult(_balance="10.0000 PXBTS",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	summary.user_block_status(node, "beos.tst.aaq", ResourceResult(_balance="",_net_weight="1376706011.7673 BEOS",_cpu_weight="1376706011.7674 BEOS",_ram_bytes=26660255448))
	summary.action_status(node.transfer(_from="beos.tst.aap",_to="beos.tst.aaq",_quantity="10.0000 PXBTS",_memo="") )
	summary.user_block_status(node, "beos.tst.aap", ResourceResult(_balance="",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	summary.user_block_status(node, "beos.tst.aaq", ResourceResult(_balance="10.0000 PXBTS",_net_weight="1376706011.7673 BEOS",_cpu_weight="1376706011.7674 BEOS",_ram_bytes=26660255448))
	summary.action_status(node.withdraw(_from="beos.tst.aaq",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aap", ResourceResult(_balance="",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=5332055448))
	summary.user_block_status(node, "beos.tst.aaq", ResourceResult(_balance="",_net_weight="1376706011.7673 BEOS",_cpu_weight="1376706011.7674 BEOS",_ram_bytes=26660255448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)