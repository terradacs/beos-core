#!/usr/bin/python3

# Scenario based on test : [2.5]-Vote-test

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

	key_aah = node.utils.create_key()
	key_aai = node.utils.create_key()

	node.add_producer_to_config("beos.tst.aah",key_aah)
	node.add_producer_to_config("beos.tst.aai",key_aai)

	node.run_node(currentdir+r"/node/[2.5]-Vote-test/", currentdir+r"/logs/[2.5]-Vote-test/")
	summary = Summarizer(currentdir+r"/[2.5]-Vote-test")

	add_handler(currentdir+r"/logs/[2.5]-Vote-test/[2.5]-Vote-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 10, [15,0,20,5,2000000], [15,0,20,5,1000000], 3000000)
	
	#Actions

	summary.action_status(node.create_account("beos.tst.aah",_activ_key=key_aah, _owner_key=key_aah) )
	summary.action_status(node.create_account("beos.tst.aai",_activ_key=key_aai, _owner_key=key_aai) )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aah",_quantity="10.0000 PXBTS",_memo="") )
	node.wait_till_block(21)
	summary.user_block_status(node, "beos.tst.aah", ResourceResult(_balance="10.0000 PXBTS",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
	summary.action_status(node.regproducer(_producer="beos.tst.aah",_producer_key=key_aah,_url="test.html",_location=0) )
	summary.action_status(node.regproducer(_producer="beos.tst.aai",_producer_key=key_aai,_url="test.html",_location=0), ActionResult(False, "transaction net usage is too high: 152 > 0") )
	summary.action_status(node.withdraw(_from="beos.tst.aah",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aah", ResourceResult(_balance="",_net_weight="1835608315.6898 BEOS",_cpu_weight="1835608315.6898 BEOS",_ram_bytes=31996305448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)