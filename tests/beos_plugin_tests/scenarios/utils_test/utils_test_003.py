#!/usr/bin/python3

import os
import sys
import time
import datetime 

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
	try:
		nr_of_accounts = 5
		nr_of_producers = 6
		node, summary, args, log = init(__file__)
		node.run_node()
		acco = node.create_accounts(nr_of_accounts, "10.0000 BTS")
		prod = node.create_producers(nr_of_producers,"10.0000 BTS")
		node.stop_node()
		acco_names = []
		prod_names = []
		for us in acco:
			acco_names.append(us.name)
		for us in prod:
			prod_names.append(us.name)

		acco_names = set(acco_names)
		prod_names = set(prod_names)

		summary.equal(nr_of_producers, len(prod_names), "len(prod_names) == {0}".format(nr_of_producers))
		summary.equal(nr_of_accounts, len(acco_names), "len(acco_names) == {0}".format(nr_of_accounts))

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)