#!/usr/bin/python3

#this test is based on `mix_test` from C++ unit tests
import os
import sys
import time
import datetime 
import requests
import json
import threading

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult
from inspect import stack

from common import get_transaction_id_from_result
from common import set_jurisdiction_for_producer

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)
		node.run_node()
		#one node with one producer
		test_prod = "eosio" #list(node.node_producers.keys())[0]


		def sample_trx(execute_on : list = None):
			call = [ "push", "action", "-f" ]
			if execute_on:
				call.append("-u")
				call.append("{}".format(execute_on))
			call.extend(["eosio.token", "transfer", '[ "{}", "eosio.null", "0.0001 BTS", "sample_description" ]'.format(test_prod), "-p", "{}".format(test_prod)])
			return node.make_cleos_call(call)

		def updateprods_rpc(new_jurs : list, execute_on : list = None):
			return set_jurisdiction_for_producer(node.get_url(), new_jurs)		

		def updateprods(new_jurs : list, execute_on : list = None):
			call = [ "push", "action", "-f" ]
			if execute_on:
				call.append("-u")
				call.append("{}".format(execute_on))
			call.extend(["eosio", "updateprod", '{"data":{"producer":"' + test_prod + '","jurisdictions":' + "{}".format(new_jurs) + '}}', "-p", "{}".format(test_prod)])
			return node.make_cleos_call(call)

		def sum_eq(result, exp_int : int = 0, exp_str : str = None):
			summary.equal(exp_int, result[0], "From line: {}".format(stack()[1].lineno))
			if exp_str:
				summary.equal(True, result[1].find(exp_str) != -1, " ### From line: {} ### ".format(stack()[1].lineno))
			log.info(" ### ### ### Log from line: {}, with result [INT]: {} ### ### ### ".format(stack()[1].lineno, result[0]))
			log.info(result[1])
		
		def sum_neq(result, exp_int : int = 0, exp_str : str = None):
			summary.equal(True, result[0] != exp_int, _additional_summarize_methodes=1)
			if exp_str:
				summary.equal(True, result[1].find(exp_str) != -1, _additional_summarize_methodes=1)
			log.info(result[1])

		def sum_rpc(result, exp_bool : bool = True, exp_str : str = None):
			if exp_bool != None:
				summary.equal(exp_bool, result['done'], _additional_summarize_methodes=1)
			if exp_str:
				summary.equal(True, result.text.find(exp_str) != -1, _additional_summarize_methodes=1)

		def next_block():
			node.wait_n_blocks(1)

		sum_eq(node.make_cleos_call(["push", "action", "eosio.token", "issue", '["{}", "100.0000 BTS", "a"]'.format(test_prod), "-p", "beos.gateway"]))

		#Beginning of the round
		node.wait_for_last_irreversible_block()

		jurisdictions = []
		for i in range(10):
			jurisdictions.append([ i, "jur{}".format(i), "desc" ])
			sum_eq(node.make_cleos_call(["push", "action", "eosio", "addjurisdict", '["{}", {}, {}, "desc"]'.
				format(test_prod, jurisdictions[i][0], jurisdictions[i][1]), "-p", "eosio"]))
		
		#1'st block
		sum_eq(updateprods([]))

		#2'nd block
		next_block()
		sum_eq(sample_trx())

		#3'rd block
		next_block()
		for i in range(1, 4):
			sum_eq(sample_trx([i]))
		sum_eq(updateprods([1, 2, 3]))

		#4'th block
		next_block()
		for i in range(1, 4):
			sum_eq(sample_trx([i]))
		sum_eq(updateprods([2,3,5]))

		#5'th block
		next_block()
		for i in range(1, 4):
			sum_eq(sample_trx([i]))
		sum_eq(updateprods([]))

		#6'th block
		next_block()
		sum_eq(sample_trx([1]))
		sum_eq(updateprods([1,2]))

		#7'th block
		next_block()
		for i in range(2, 0, -1):
			sum_eq(sample_trx([i]))
		sum_eq(updateprods([3, 2, 1]))

		#8'th block
		next_block()
		for i in range(2, 0, -1):
			sum_eq(sample_trx([i]))
		sum_eq(updateprods([4, 5]))

		#9'th block
		next_block()
		for i in range(2, 0, -1):
			sum_eq(sample_trx([i]))
		sum_eq(updateprods([1, 2, 3]))
		sum_eq(sample_trx([3]))
		sum_eq(updateprods([3]))

		#10'th block
		next_block()
		sum_eq(sample_trx([2]))
		sum_eq(updateprods([1,2,3]))
		sum_eq(sample_trx([3]))
		sum_eq(sample_trx([1]))
		sum_eq(updateprods([3,2,4,5,1]))
		sum_eq(sample_trx([1,3,4]))
		sum_eq(updateprods([3,4,5,1]))

		#11'th block
		next_block()
		sum_eq(sample_trx([1,2,3]))
		sum_eq(updateprods([1,2,3,4]))
		sum_eq(sample_trx([3]))
		sum_eq(sample_trx([5]))

		#12'th block
		next_block()
		sum_eq(sample_trx([2]))
		sum_eq(updateprods([1,2,3]))
		sum_eq(updateprods([1,2,3, 4], [3]))
		sum_eq(updateprods([1,2,3], [3]))
		sum_eq(updateprods([1,2]))
		sum_eq(updateprods([2]))
		sum_eq(updateprods([2,3]))

		#13't block
		next_block()
		sum_eq(sample_trx([0]))
		sum_eq(sample_trx([1]))
		sum_eq(updateprods([3,2,1,0]))
		sum_eq(sample_trx([3]))
		sum_eq(sample_trx([1,2,3,4,5,6]))
		sum_eq(updateprods([6,5,4,3,2,1,0]))
		sum_eq(updateprods([6,1,3,0]))
		sum_eq(updateprods([1,3,0]))
		sum_eq(updateprods([1,3]))
		
		#14'th block
		next_block()
		sum_eq(sample_trx())
		sum_eq(sample_trx())
		sum_eq(updateprods([0]))
		sum_eq(updateprods([1]))
		sum_eq(updateprods([0]))
		sum_eq(sample_trx())

		#15'th block
		next_block()
		sum_eq(sample_trx([0,1,2]))
		sum_eq(updateprods([0]))
		sum_eq(updateprods([1]))
		sum_eq(updateprods([2]))
		sum_eq(updateprods([0,1]))
		sum_eq(updateprods([3]))

		#16'th block
		next_block()
		sum_eq(sample_trx([1]))
		sum_eq(sample_trx([2,3]))
		sum_eq(updateprods([4]))
		sum_eq(updateprods([4,1]))
		sum_eq(updateprods([2,3]))
		sum_eq(updateprods([1,2,3,4]))
		sum_eq(sample_trx([4]))
		sum_eq(updateprods([1,2,3]))
		sum_eq(updateprods([4,2,3]))
		sum_eq(updateprods([1,4]))
		sum_eq(updateprods([1,2,4,5]))
		sum_eq(sample_trx([5]))
		sum_eq(updateprods([1,2,3,4]))

		#17'th block
		next_block()
		sum_eq(updateprods([1], [0]))
		sum_eq(updateprods([2,0], [1]))
		sum_eq(updateprods([3,1,0], [2]))
		sum_eq(updateprods([4,2,1,0], [3]))

		#18'th block
		next_block()
		sum_eq(updateprods([1,2,3],[0]))
		sum_eq(updateprods([1,2,3,4,0],[2,3]))
		sum_eq(updateprods([0,1]))
		sum_eq(updateprods([2,3]))
		sum_eq(updateprods([7,8],[1,2,3]))
		sum_eq(updateprods([7,8,2,0],[4]))
		sum_eq(updateprods([4,0,3],[7]))
		sum_eq(updateprods([0,2,3,4,7],[8]))
		sum_eq(updateprods([0,2,3,4,7, 1],[0,2,3,4,7,1,8]))
		sum_eq(updateprods([0,2,3,4,8,7,1],[0,2,3,4,7,1,8]))

		#19'th block
		next_block()
		sum_eq(updateprods([1]))
		sum_eq(sample_trx([0]))


	except Exception as _ex:
		log.exception(_ex)
		summary.equal(False, True, "Exception occured durring testing: {}.".format(_ex))
	finally:
		status = summary.summarize()
		node.stop_node()
		exit(status)