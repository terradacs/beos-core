#!/usr/bin/python3

import os
import sys
import time
import datetime 
import requests

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, init_cluster, ActionResult, ResourceResult, VotersResult

if __name__ == "__main__":
	try:
		number_of_pnodes  = 3
		producer_per_node = 1
		cluster, summary, args, log = init_cluster(__file__, number_of_pnodes, producer_per_node)
		cluster.run_all()
		code, mess = cluster.bios.make_cleos_call(["get", "info"])

		prods=[]
		for prod, data in cluster.producers.items(): 
			prods.append(prod)

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "0", "POLAND", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "1", "GERMANY", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "2", "RUSSIA", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

		call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[0]}} }}'.format(prods[0]), "-p", "{0}".format(prods[0])]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

		call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[1]}} }}'.format(prods[1]), "-p", "{0}".format(prods[1])]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

		call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[2]}} }}'.format(prods[2]), "-p", "{0}".format(prods[2])]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

		call =[ "push", "action", "--jurisdictions", "[0]", "beos.gateway", "issue", "[ \"{0}\", \"100.0000 BTS\", \"hello\" ]".format(prods[0]), "-p", "beos.gateway"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

		call =[ "push", "action", "--jurisdictions", "[1]", "beos.gateway", "issue", "[ \"{0}\", \"100.0000 BTS\", \"hello\" ]".format(prods[1]), "-p", "beos.gateway"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

		call =[ "push", "action", "--jurisdictions", "[2]","beos.gateway", "issue", "[ \"{0}\", \"100.0000 BTS\", \"hello\" ]".format(prods[2]), "-p", "beos.gateway"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))
		summary.equal(True, code == 0, "This call {0} should succeed".format(call) )

	except Exception as _ex:
		log.exception(_ex)
		summary.equal(False, True, "Exception occured durring testing.")
	finally:
		status = summary.summarize()
		cluster.stop_all()
		exit(status)