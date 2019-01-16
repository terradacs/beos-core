#!/usr/bin/python3

# Scenario based on test : [2.10]-Vote-test

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

	key_aaj = node.utils.create_key()
	key_aak = node.utils.create_key()	
	key_aam = node.utils.create_key()

	node.add_producer_to_config("beos.tst.aaj", key_aaj)
	node.add_producer_to_config("beos.tst.aak", key_aak)
	node.add_producer_to_config("beos.tst.aam", key_aam)

	node.run_node(currentdir+r"/node/[2.10]-Vote-test/", currentdir+r"/logs/[2.10]-Vote-test/")
	summary = Summarizer(currentdir+r"/[2.10]-Vote-test")

	add_handler(currentdir+r"/logs/[2.10]-Vote-test/[2.10]-Vote-test")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 10, [15,0,20,5,2000000], [15,0,20,5,1000000], 3000000)
	
	#Actions
	summary.action_status(node.create_account("beos.tst.aaj",_activ_key=key_aaj, _owner_key=key_aaj) )
	summary.action_status(node.create_account("beos.tst.aak",_activ_key=key_aak, _owner_key=key_aak) )
	summary.action_status(node.create_account("beos.tst.aam",_activ_key=key_aam, _owner_key=key_aam) )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aaj",_quantity="10.0000 PXBTS",_memo="") )
	summary.action_status(node.issue(_from="beos.gateway",_to="beos.tst.aak",_quantity="10.0000 PXBTS",_memo="") )
	node.wait_till_block(25)
	summary.action_status(node.regproducer(_producer="beos.tst.aaj",_producer_key=key_aaj,_url="test.html",_location=0) )
	summary.action_status(node.voteproducer(_voter="beos.tst.aak",_proxy="",_producers=['beos.tst.aaj']) )
	summary.action_status(node.voteproducer(_voter="beos.tst.aam",_proxy="",_producers=['beos.tst.aaj']), ActionResult(False, "user must stake before they can vote") )
	summary.action_status(node.voteproducer(_voter="beos.tst.aaj",_proxy="",_producers=['beos.tst.aak']), ActionResult(False, "producer is not registered") )
	summary.user_block_status(node, "beos.tst.aaj", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804157.8448 BEOS",_cpu_weight="917804157.8450 BEOS",_ram_bytes=15998155448))
	summary.user_block_status(node, "beos.tst.aak", ResourceResult(_balance="10.0000 PXBTS",_net_weight="917804157.8448 BEOS",_cpu_weight="917804157.8450 BEOS",_ram_bytes=15998155448))
	summary.user_block_status(node, "beos.tst.aam", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary.action_status(node.voteproducer(_voter="beos.tst.aaj",_proxy="",_producers=['beos.tst.aaj']) )
	summary.action_status(node.withdraw(_from="beos.tst.aaj",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	summary.action_status(node.withdraw(_from="beos.tst.aak",_bts_to="any_account",_quantity="10.0000 PXBTS",_memo="_memo") )
	
	#At end
	summary.user_block_status(node, "beos.tst.aaj", ResourceResult(_balance="",_net_weight="917804157.8448 BEOS",_cpu_weight="917804157.8450 BEOS",_ram_bytes=15998155448))
	summary.user_block_status(node, "beos.tst.aak", ResourceResult(_balance="",_net_weight="917804157.8448 BEOS",_cpu_weight="917804157.8450 BEOS",_ram_bytes=15998155448))
	summary.user_block_status(node, "beos.tst.aam", ResourceResult(_balance="",_net_weight="0.0000 BEOS",_cpu_weight="0.0000 BEOS",_ram_bytes=5448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)