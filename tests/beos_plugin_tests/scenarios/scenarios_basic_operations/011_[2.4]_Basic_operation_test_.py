#!/usr/bin/python3

# Scenario based on test : [2.4]-Basic-operation-test

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

	node.run_node(currentdir+r"/node/[2.4]-Basic-operation-test/", currentdir+r"/logs/[2.4]-Basic-operation-test/")
	summary = Summarizer(currentdir+r"/[2.4]-Basic-operation-test")

	add_handler(currentdir+r"/logs/[2.4]-Basic-operation-test/[2.4]-Basic-operation-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 40, [20,0,35,15,2000000], [20,0,35,15,1000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aan") )
	summary.action_status(node.create_account("beos.tst.aao") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aan",_quantity="10.0000 PXBTS",_memo="") )
	summary.user_block_status(node, "beos.tst.aan", ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.user_block_status(node, "beos.tst.aao", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	node.wait_till_block(25)
	summary.action_status(node.transfer(_from="beos.tst.aan",_to="beos.tst.aao",_quantity="10.0000 PXBTS",_memo="any_memo") )
	node.wait_till_block(30)
	summary.action_status(node.transfer(_from="beos.tst.aao",_to="beos.tst.aan",_quantity="10.0000 PXBTS",_memo="any_memo"), ActionResult(False, "transaction net usage is too high: 136 > 0") )
	summary.user_block_status(node, "beos.tst.aan", ResourceResult(_balance="",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
	summary.user_block_status(node, "beos.tst.aao", ResourceResult(_balance="10.0000 PXBTS",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	node.wait_till_block(40)
	summary.action_status(node.transfer(_from="beos.tst.aao",_to="beos.tst.aan",_quantity="10.0000 PXBTS",_memo="any_memo") )
	summary.user_block_status(node, "beos.tst.aan", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
	summary.user_block_status(node, "beos.tst.aao", ResourceResult(_balance="",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
	summary.action_status(node.withdraw(_from="beos.tst.aan",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aan", ResourceResult(_balance="",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
	summary.user_block_status(node, "beos.tst.aao", ResourceResult(_balance="",_net_weight="917804157.8449 BEOS",_cpu_weight="917804157.8449 BEOS",_ram_bytes=15998155448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)