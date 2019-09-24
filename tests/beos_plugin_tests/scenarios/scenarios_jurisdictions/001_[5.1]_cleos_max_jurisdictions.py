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
		node.run_node()
		REQ_ERROR = "Too many jurisdictions given, max value is 255."
		MAX_JURISDICTIONS = 255
		juris = [x for x in range(MAX_JURISDICTIONS + 1)]
		juris = "{0}".format(juris)

		new_user = node.generate_user_name()
		calls = [["system", "newaccount", "beos.gateway", new_user, "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV", "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV", "--transfer-ram", "-u", "{0}".format(juris)],
				["system", "newaccount", "beos.gateway", new_user, "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV", "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV", "--transfer-ram", "--jurisdictions", "{0}".format(juris)]]
		for call in calls:
			result, mess = node.make_cleos_call(call)
			log.info("Call retcode {0} and {1}".format(result, mess))
			summary.equal(True, result != 0, "This `{0}` call must fail.".format(" ".join(call)))
			summary.equal(True, mess.find(REQ_ERROR) != 0, "This call `{0}` must have `{1}` error message.".format(" ".join(call), REQ_ERROR))

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
		summary.equal(False, True, "Exception occured durring testing.")
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)