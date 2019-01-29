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
		node, summary, args, log = init(__file__)

		start = node.run_node()
		summary.equal(True, start != 0, "start != 0")
		node_running = node.node_is_running
		summary.equal(True, node_running == True, "node_running == True")
		node.stop_node()
		node_running = node.node_is_running
		summary.equal(True, node_running == False, "node_running == False")

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)