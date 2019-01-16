#!/usr/bin/python3

# Scenario based on test : [3.1]-Vote-test

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

	key_abc = node.utils.create_key()
	key_abd = node.utils.create_key()	

	node.add_producer_to_config("beos.tst.abc", key_abc)
	node.add_producer_to_config("beos.tst.abd", key_abd)
	node.run_node(currentdir+r"/node/[3.1]-Vote-test/", currentdir+r"/logs/[3.1]-Vote-test/")
	summary = Summarizer(currentdir+r"/[3.1]-Vote-test")

	add_handler(currentdir+r"/logs/[3.1]-Vote-test/[3.1]-Vote-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 1, [10,0,20,10,8000000], [10,0,18,4,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abc",_activ_key=key_abc, _owner_key=key_abc) )
	summary.action_status(node.create_account("beos.tst.abd",_activ_key=key_abd, _owner_key=key_abd) )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.abc",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.abd",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.regproducer(_producer="beos.tst.abc",_producer_key=key_abc,_url="http://fake.html",_location=0), ActionResult(False, "transaction net usage is too high: 160 > 0") )
	summary.action_status(node.voteproducer(_voter="beos.tst.abd",_proxy="",_producers=['beos.tst.abd']), ActionResult(False, "user must stake before they can vote") )
	node.wait_till_block(11)
	summary.action_status(node.regproducer(_producer="beos.tst.abc",_producer_key=key_abc,_url="http://fake.html",_location=0) )
	node.wait_till_block(12)
	summary.action_status(node.regproducer(_producer="beos.tst.abd",_producer_key=key_abd,_url="http://fake.html",_location=0) )
	node.wait_till_block(15)
	summary.action_status(node.voteproducer(_voter="beos.tst.abd",_proxy="",_producers=['beos.tst.abc']) )
	summary.action_status(node.voteproducer(_voter="beos.tst.abc",_proxy="",_producers=['beos.tst.abd']) )
	node.wait_till_block(20)
	summary.action_status(node.withdraw(_from="beos.tst.abc",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="_memo") )
	summary.action_status(node.withdraw(_from="beos.tst.abd",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abc", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.user_block_status(node, "beos.tst.abd", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)