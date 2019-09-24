#!/usr/bin/python3

import os
import sys
import json
import time
import datetime 

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)
		node.run_node()
		acc = node.create_accounts(1)
		node_info = json.loads(node.make_cleos_call("get info"))
		acc_info = json.loads(node.make_cleos_call("get account {0} -j".format(acc[0].name)))
		node.stop_node()

		summary.equal(True, "chain_id" in node_info, "\"chain_id\" in node_info")
		summary.equal(True, acc_info["account_name"] == acc[0].name, "acc_info[\"account_name\"] == {0}".format(acc[0].name))

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)