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
		node, summary, args, log = init(__file__)
		node.run_node()
		acc = node.create_producers(nr_of_accounts,"10.0000 PXBTS")
		node.stop_node()
		names = []
		for ac in acc:
			names.append(ac.name)

		names = set(names)

		summary.equal(nr_of_accounts, len(names), "len(names) == {0}".format(nr_of_accounts))

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)