#!/usr/bin/python3

# Scenario based on test : [6.2]-Undelegatebw---after-distribution-period---to-self,-with-voting

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

	node.run_node(currentdir+r"/node/[6.2]-Undelegatebw---after-distribution-period---to-self,-with-voting/", currentdir+r"/logs/[6.2]-Undelegatebw---after-distribution-period---to-self,-with-voting/")
	summary = Summarizer(currentdir+r"/[6.2]-Undelegatebw---after-distribution-period---to-self,-with-voting")

	add_handler(currentdir+r"/logs/[6.2]-Undelegatebw---after-distribution-period---to-self,-with-voting/[6.2]-Undelegatebw---after-distribution-period---to-self,-with-voting")
	
	#Changeparams
	node.changeparams(["0.0000 PXBTS"], 1, [10,0,30,5,8000000], [10,0,20,5,5000000], 3000000)
	
	#Actions
	key = node.utils.create_key()
	summary.action_status(node.create_account("beos.tst.abp",_activ_key=key, _owner_key=key) )
	summary.action_status(node.issue(_to="beos.tst.abp",_quantity="5.0000 PXBTS",_memo="",_from="beos.gateway") )
	node.wait_till_block(15)
	summary.action_status(node.voteproducer(_voter="beos.tst.abp",_proxy="",_producers=['beos.tst.abp']), ActionResult(False, "producer is not registered") )
	node.wait_till_block(16)
	summary.action_status(node.regproducer(_producer="beos.tst.abp",_producer_key=key,_url="test3.html",_location="0") )
	node.wait_till_block(35)
	summary.action_status(node.undelegatebw(_from="beos.tst.abp",_receiver="beos.tst.abp",_unstake_net_quantity="1.0000 BEOS",_unstake_cpu_quantity="1.0000 BEOS"), ActionResult(False, "cannot undelegate bandwidth until the chain is activated (at least 15% of all tokens participate in voting)") )
	summary.action_status(node.withdraw(_from="beos.tst.abp",_bts_to="any_account",_quantity="5.0000 PXBTS",_memo="") )
	
	#At end
	summary.user_block_status(node, "beos.tst.abp", ResourceResult(_balance="",_net_weight="1835608015.6896 BEOS",_cpu_weight="1835608015.6900 BEOS",_ram_bytes=31992305448))
	summary_status = summary.summarize()
	node.stop_node()
	exit(summary_status)