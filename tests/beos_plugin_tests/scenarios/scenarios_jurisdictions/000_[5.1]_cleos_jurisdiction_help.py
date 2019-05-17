#!/usr/bin/python3

# Scenario based on test : [6.1]-Undelegatebw---after-distribution-period---to-self,-without-voting

import os
import sys
import time
import datetime 

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)

		look_for = "-u,--jurisdictions TEXT"

		call = ["push", "action", "--help"]
		result = node.make_cleos_call(call)
		log.info(result)
		summary.equal(True, result.find(look_for) != -1, "Push action should contain `jurisdiction` option.")

		call = ["push", "transaction", "--help"]
		result = node.make_cleos_call(call)
		log.info(result)
		summary.equal(True, result.find(look_for) != -1, "Push transaction should contain `jurisdiction` option.")

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
		summary.equal(False, True, "Exception occured durring testing.")
	finally:
		summary_status = summary.summarize()
		exit(summary_status)