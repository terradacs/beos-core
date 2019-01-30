
import os
import sys
import time
import datetime 

from concurrent.futures import ThreadPoolExecutor

class Info(object):
	def __init__(self, is_creation, items, length, is_reg_producer, is_vote_producer, is_unreg_producer = False, is_failed = False, fail_message = "" ):
		self.is_creation = is_creation
		self.items = items
		self.length = length
		self.is_reg_producer = is_reg_producer
		self.is_vote_producer = is_vote_producer
		self.is_unreg_producer = is_unreg_producer
		self.is_failed = is_failed
		self.fail_message = fail_message

def get_producers_stats( node, log = None ):

	start = ""
	nr_prods = 0
	nr_voted_prods = 0

	rpc = node.get_url_caller()

	while True:
		_start = "%s" % ( start )
		data = {"json":"true", "lower_bound":_start, "limit":1000}

		rpc_result = rpc.chain.get_producers( data )	

		nr_prods += len( rpc_result["rows"] )

		for prod in rpc_result["rows"]:
			vote = float( prod["total_votes"] )
			if vote > 0:
				nr_voted_prods += 1

		if len( rpc_result["more"] ) == 0:
			break

		start = rpc_result["more"]

	return nr_prods, nr_voted_prods

def worker_creator( node, summary, items, info, log ):
	result = node.create_accounts( 1, "1.0000 PXBTS" )
	for i in result:
		items.append( i )

def worker_operation( node, summary, item, info, log ):
	if info.is_failed:

		fail_action = ActionResult( False, info.fail_message )

		if info.is_reg_producer:
			summary.action_status(node.regproducer(_producer=item.name,_producer_key=item.akey,_url="test.html",_location=0), fail_action )

		if info.is_vote_producer:
			summary.action_status(node.voteproducer(_voter=item.name,_proxy="",_producers=[item.name]), fail_action )

		if info.is_unreg_producer:
			summary.action_status(node.unregprod(_producer=item.name), fail_action )
	else:
		if info.is_reg_producer:
			summary.action_status(node.regproducer(_producer=item.name,_producer_key=item.akey,_url="test.html",_location=0) )

		if info.is_vote_producer:
			summary.action_status(node.voteproducer(_voter=item.name,_proxy="",_producers=[item.name]) )

		if info.is_unreg_producer:
			summary.action_status(node.unregprod(_producer=item.name) )

def execute( node, summary, callable, threads, info, log = None ):
	cnt = 0
	done = False

	while True:
		with ThreadPoolExecutor( max_workers = threads ) as executor:
			for i in range( threads ):

				if info.is_creation:
					future = executor.submit( callable, node, summary, info.items, info, log )
				else:
					future = executor.submit( callable, node, summary, info.items[cnt], info, log )

				cnt += 1

				if ( cnt % 100 ) == 0:
					time.sleep(1)

				if cnt >= info.length:
					done = True
					break

		if done:
			break
