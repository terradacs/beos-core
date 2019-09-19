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

		acc = node.create_accounts(1,"10.0000 BTS")
		node.run_node()
		dict1 = {"key1":"key1"}
		dict2 = {"key1":"key1"}

		summary.equal(False, 1==2, "1==2")
		summary.equal(True,  1==1, "1==1")
		summary.equal(False, 1==2)
		summary.equal(True,  1==1)

		summary.equal(True, dict1.keys() == dict2.keys(), "dict1.keys() == dict2.keys()")
		summary.equal(False, dict1.keys() != dict2.keys(), "dict1.keys() != dict2.keys()")

		summary.equal(True, dict1["key1"] == dict1["key1"], "dict1[\"key1\"] == dict1[\"key1\"]")
		summary.equal(True, dict2["key1"] == dict1["key1"], "dict2[\"key1\"] == dict1[\"key1\"]")
		summary.equal(True, dict1["key1"] == dict2["key1"])
		summary.equal(True, dict2["key1"] == dict2["key1"], "dict2[\"key1\"] == dict2[\"key1\"]")

		summary.equal(3, 2+1, "2+1")
		summary.equal(1, 2-1, "2-1")

		rpc = node.get_url_caller()
		data = {"account":acc[0].name,"symbol":"BTS", "code":"eosio.token"}
		res = rpc.chain.get_currency_balance(data)
		log.info("res {0}".format(res))

		summary.equal(True, "10.0000 BTS" == res[0], "\"10.0000 BTS\" == res[0]")
		summary.equal(True, "10.0000 BTS" == res[0])

		#summary.equal(False, "10.0000 BTS" == res[0], "\"10.0000 BTS\" == res[0]")
		#summary.equal(False, "10.0000 BTS" == res[0])

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)