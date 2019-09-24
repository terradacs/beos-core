#!/usr/bin/python3

# Scenario based on test : [2.5]-Vote-test

import os
import sys
import time
import datetime 

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult
from beos_test_utils.utility_misc import *

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)

		accounts_small_set = []
		accounts_big_set = []

		nr_system_producers = 10
		nr_accounts_small_set = 10
		nr_accounts_big_set = 40

		producers = node.create_producers( nr_system_producers, "1.0000 BTS" )
		node.run_node()

		#Changeparams
		newparams = {
			"beos" : {
				"starting_block" : 5,
				"next_block" : 0, 
				"ending_block" : 200000,
				"block_interval" : 5, 
				"trustee_reward" : 0
			},
			"ram" : {
				"starting_block" : 5,
				"next_block" : 0, 
				"ending_block" : 200000,
				"block_interval" : 5, 
				"trustee_reward" : 0 
			},
			"proxy_assets" : [ "0.0000 BTS"],
			"ram_leftover" : 3000000,
			"starting_block_for_initial_witness_election":10
		}
		node.changeparams( newparams )

		node.wait_till_block( 6 )

		#Actions
		threads = 10
		is_creation = True
		is_reg_producer = False
		is_vote_producer = False
		is_unreg_producer = False

		info = Info( is_creation, accounts_small_set, nr_accounts_small_set, is_reg_producer, is_vote_producer )
		execute( node, summary, worker_creator, threads, info, log )
		node.wait_n_blocks( 2 )

		info = Info( is_creation, accounts_big_set, nr_accounts_big_set, is_reg_producer, is_vote_producer )
		execute( node, summary, worker_creator, threads, info, log )
		node.wait_n_blocks( 2 )

		is_creation = False
		is_reg_producer = True

		info = Info( is_creation, accounts_small_set, nr_accounts_small_set, is_reg_producer, is_vote_producer )
		execute( node, summary, worker_operation, threads, info, log )
		node.wait_n_blocks( 2 )

		info2 = Info( is_creation, producers, nr_system_producers, is_reg_producer, is_vote_producer )
		execute( node, summary, worker_operation, threads, info2, log )
		node.wait_n_blocks( 2 )

		is_reg_producer = False
		is_unreg_producer = True

		info = Info( is_creation, accounts_small_set, nr_accounts_small_set, is_reg_producer, is_vote_producer, is_unreg_producer )
		execute( node, summary, worker_operation, threads, info, log )
		node.wait_n_blocks( 2 )

		info2 = Info( is_creation, producers, nr_system_producers, is_reg_producer, is_vote_producer, is_unreg_producer )
		execute( node, summary, worker_operation, threads, info2, log )
		node.wait_n_blocks( 2 )

		is_vote_producer = True
		is_unreg_producer = False
		is_failed = True
		fail_message = "producer is not currently registered"
		info = Info( is_creation, producers, nr_system_producers, is_reg_producer, is_vote_producer, is_unreg_producer, is_failed, fail_message )
		execute( node, summary, worker_operation, threads, info, log )

		node.wait_n_blocks( 10 )

		rpc_nr_producers, rpc_nr_voted_producers = get_producers_stats( node, log )

		what = "Incorrect number of producents: rpc: %s created: %s \n" % ( rpc_nr_producers, nr_accounts_small_set + nr_system_producers + 1 )
		summary.equal( rpc_nr_producers, nr_system_producers + nr_accounts_small_set + 1, what )

		what = "Incorrect number of voted producents: rpc: %s voted: %s \n" % ( rpc_nr_voted_producers, nr_system_producers )
		summary.equal( rpc_nr_voted_producers, 0, what )

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)