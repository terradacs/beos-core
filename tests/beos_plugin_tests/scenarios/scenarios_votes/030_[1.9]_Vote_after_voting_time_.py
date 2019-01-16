#!/usr/bin/python3

# Scenario based on test : [1.9]-Vote-after-voting-time

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

	key_abv = node.utils.create_key()
	key_abw = node.utils.create_key()	
	key_abx = node.utils.create_key()

	node.add_producer_to_config("beos.tst.abv", key_abv)
	node.add_producer_to_config("beos.tst.abw", key_abw)
	node.add_producer_to_config("beos.tst.abx", key_abx)

	node.run_node(currentdir+r"/node/[1.9]-Vote-after-voting-time/", currentdir+r"/logs/[1.9]-Vote-after-voting-time/")
	summary = Summarizer(currentdir+r"/[1.9]-Vote-after-voting-time")

	add_handler(currentdir+r"/logs/[1.9]-Vote-after-voting-time/[1.9]-Vote-after-voting-time")

	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 20, [10,0,20,10,8000000], [10,0,20,10,5000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.abv",_activ_key=key_abv, _owner_key=key_abv) )
	summary.action_status(node.create_account("beos.tst.abw",_activ_key=key_abw, _owner_key=key_abw) )
	summary.action_status(node.create_account("beos.tst.abx",_activ_key=key_abx, _owner_key=key_abx) )
	summary.action_status(node.issue(_to="beos.tst.abv",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.issue(_to="beos.tst.abx",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	summary.action_status(node.regproducer(_producer="beos.tst.abx",_producer_key=key_abx,_url="test0.html",_location=0), ActionResult(False, "") )
	summary.action_status(node.regproducer(_producer="beos.tst.abx",_producer_key=key_abx,_url="test1.html",_location=0), ActionResult(False, "") )
	node.wait_till_block(25)
	summary.action_status(node.regproducer(_producer="beos.tst.abx",_producer_key=key_abx,_url="test2.html",_location=0) )
	summary.action_status(node.regproducer(_producer="beos.tst.abx",_producer_key=key_abx,_url="test3.html",_location=0) )
	summary.action_status(node.voteproducer(_voter="beos.tst.abw",_proxy="",_producers=['beos.tst.abx']), ActionResult(False, "") )
	summary.action_status(node.voteproducer(_voter="beos.tst.abv",_proxy="",_producers=['beos.tst.abx']) )
	summary.action_status(node.voteproducer(_voter="beos.tst.abx",_proxy="",_producers=['beos.tst.abx']) )
	summary.action_status(node.voteproducer(_voter="beos.tst.abx",_proxy="",_producers=['beos.tst.abv']), ActionResult(False, "") )
	summary.action_status(node.voteproducer(_voter="beos.tst.abx",_proxy="",_producers=['beos.tst.abw']), ActionResult(False, "") )
	summary.action_status(node.voteproducer(_voter="beos.tst.abw",_proxy="",_producers=['beos.tst.abw']), ActionResult(False, "") )
	summary.action_status(node.voteproducer(_voter="beos.tst.abv",_proxy="",_producers=['beos.tst.abv']), ActionResult(False, "") )
	summary.action_status(node.withdraw(_from="beos.tst.abv",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="") )
	summary.action_status(node.withdraw(_from="beos.tst.abx",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abv", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary.user_block_status(node, "beos.tst.abw", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.user_block_status(node, "beos.tst.abx", ResourceResult(_balance="",_net_weight="917804007.8448 BEOS",_cpu_weight="917804007.8450 BEOS",_ram_bytes=15996155448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)