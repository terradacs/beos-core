#!/usr/bin/python3

# Scenario based on test : [1.6]-Vote-test

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


	key_aaz = node.utils.create_key()	
	key_aba = node.utils.create_key()

	node.add_producer_to_config("beos.tst.aaz", key_aaz)
	node.add_producer_to_config("beos.tst.aba", key_aba)

	node.run_node(currentdir+r"/node/[1.6]-Vote-test/", currentdir+r"/logs/[1.6]-Vote-test/")
	summary = Summarizer(currentdir+r"/[1.6]-Vote-test")

	add_handler(currentdir+r"/logs/[1.6]-Vote-test/[1.6]-Vote-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 20, [30,0,40,10,8000000], [30,0,40,10,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aaz",_activ_key=key_aaz, _owner_key=key_aaz) )
	summary.action_status(node.create_account("beos.tst.aba",_activ_key=key_aba, _owner_key=key_aba) )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aaz",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aba",_quantity="5.0000 PXBTS",_memo="") )
	node.wait_till_block(30)
	summary.action_status(node.voteproducer(_voter="beos.tst.aba",_proxy="",_producers=['beos.tst.aaz']), ActionResult(False, "producer is not registered") )
	node.wait_till_block(32)
	summary.action_status(node.voteproducer(_voter="beos.tst.aba",_proxy="",_producers=['beos.tst.aba']), ActionResult(False, "producer is not registered") )
	summary.action_status(node.voteproducer(_voter="beos.tst.aba",_proxy="",_producers=['beos.tst.abb']), ActionResult(False, "producer is not registered") )
	node.wait_till_block(36)
	summary.action_status(node.regproducer(_producer="beos.tst.aaz",_producer_key=key_aaz,_url="test.html",_location="0") )
	summary.user_block_status(node, "beos.tst.aaz", ResourceResult(_balance="5.0000 PXBTS",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=7998080448))
	summary.user_block_status(node, "beos.tst.aba", ResourceResult(_balance="5.0000 PXBTS",_net_weight="458902003.9224 BEOS",_cpu_weight="458902003.9225 BEOS",_ram_bytes=7998080448))
	node.wait_till_block(42)
	summary.action_status(node.regproducer(_producer="beos.tst.aaz",_producer_key=key_aaz,_url="test2.html",_location="0") )
	summary.action_status(node.voteproducer(_voter="beos.tst.abb",_proxy="",_producers=['beos.tst.aaz']), ActionResult(False, "producer is not registered") )
	summary.action_status(node.voteproducer(_voter="beos.tst.aba",_proxy="",_producers=['beos.tst.aaz']) )
	summary.action_status(node.regproducer(_producer="beos.tst.aba",_producer_key=key_aba,_url="test3.html",_location="0") )
	summary.action_status(node.voteproducer(_voter="beos.tst.aba",_proxy="",_producers=['beos.tst.aaz']) )
	summary.action_status(node.voteproducer(_voter="beos.tst.aba",_proxy="",_producers=['beos.tst.abb']), ActionResult(False, "producer is not registered") )
	summary.action_status(node.transfer(_from="beos.tst.aba",_to="beos.tst.aaz",_quantity="6.0000 PXBTS",_memo="any_memo"), ActionResult(False, "overdrawn balance") )
	summary.action_status(node.transfer(_from="beos.tst.aba",_to="beos.tst.aaz",_quantity="5.0000 PXBTS",_memo="any_memo") )
	summary.action_status(node.voteproducer(_voter="beos.tst.aba",_proxy="",_producers=['beos.tst.aaz']) )
	summary.action_status(node.withdraw(_from="beos.tst.aaz",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aaz", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.user_block_status(node, "beos.tst.aba", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)