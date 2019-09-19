#!/usr/bin/python3

import os
import sys
import time
import datetime 

if os.path.exists(os.path.dirname(os.path.abspath(__file__))+ "/logs/"+ __file__):
    exit(0)

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)

		summary.action_status(ActionResult(True,""), ActionResult(True,""))
		summary.action_status(ActionResult(False,"wrong message"), ActionResult(False,"wrong message"))
		summary.equal(True, ActionResult(True,"").compare(ActionResult(True,"")), "ActionResult(True,\"\").compare(ActionResult(True,\"\"))")
		summary.equal(True, ActionResult(False,"").compare(ActionResult(False,"")), "ActionResult(False,\"\").compare(ActionResult(False,\"\"))")
		summary.equal(True, ActionResult(False,"wrong message").compare(ActionResult(False,"wrong message")), "ActionResult(False,\"wrong message\").compare(ActionResult(False,\"wrong message\"))")

		summary.equal(False, ActionResult(True,"").compare(ActionResult(False,"")), "ActionResult(True,\"\").compare(ActionResult(False,\"\"))")
		summary.equal(False, ActionResult(False,"").compare(ActionResult(True,"")), "ActionResult(False,\"\").compare(ActionResult(True,\"\"))")
		summary.equal(False, ActionResult(False,"2 message wrong").compare(ActionResult(False,"wrong message 2 ")), "ActionResult(False,\"2 message wrong\").compare(ActionResult(False,\"wrong message 2\"))")

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)