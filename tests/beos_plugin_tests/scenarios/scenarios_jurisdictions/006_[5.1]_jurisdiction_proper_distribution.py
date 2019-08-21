#!/usr/bin/python3

import os
import sys
import time
import json
import datetime 
import requests

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, init_cluster, ActionResult, ResourceResult, VotersResult
from beos_test_utils.beos_utils_pack import get_transaction_id_from_result

if __name__ == "__main__":
	try:
		number_of_pnodes  = 3
		producer_per_node = 1
		cluster, summary, args, log = init_cluster(__file__, number_of_pnodes, producer_per_node)
		cluster.run_all()

		prods=[]
		for prod, data in cluster.producers.items(): 
			prods.append(prod)

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "0", "POLAND", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "1", "GERMANY", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "2", "RUSSIA", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))

		prods_0_jurisdiction = 0
		prods_1_jurisdiction = 1
		prods_2_jurisdiction = 2

		cluster.bios.wait_for_last_irreversible_block() 

		call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[{1}]}} }}'.format(prods[0], prods_0_jurisdiction), "-p", "{0}".format(prods[0])]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))

		call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[{1}]}} }}'.format(prods[1], prods_1_jurisdiction), "-p", "{0}".format(prods[1])]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))

		call = ["push", "action", "eosio", "updateprod", '{{"data":{{"producer":"{0}", "jurisdictions":[{1}]}} }}'.format(prods[2], prods_2_jurisdiction), "-p", "{0}".format(prods[2])]
		code, result = cluster.bios.make_cleos_call(call)
		log.info("{0}".format(result))

		call =[ "push", "action", "--jurisdictions", "[{0}]".format(prods_1_jurisdiction), "beos.gateway", "issue", "[ \"{0}\", \"111.0000 BTS\", \"hello\" ]".format(prods[0]), "-p", "beos.gateway"]
		code, result = cluster.bios.make_cleos_call(call, False)
		log.info("{0}".format(result))

		trx_id = get_transaction_id_from_result(code, result)
		log.info("Waiting for transaction id: {} in block".format(trx_id))
		block = cluster.bios.wait_for_transaction_in_block(trx_id)

		call = ["get", "block", "{0}".format(block)]
		code, result = cluster.bios.make_cleos_call(call)
		log.info(result)
		result = json.loads(result)
		summary.equal(True, result["producer"] == "{0}".format(prods[1]), "This transaction should be signed by producer {0}".format(prods[1]))

		call = ["get", "producer_jurisdiction_for_block", "{0}".format(prods[1]), "{0}".format(block)]
		code, result = cluster.bios.make_cleos_call(call)
		log.info(result)
		result = json.loads(result)
		summary.equal(True, prods_1_jurisdiction in result["producer_jurisdiction_for_block"][0]["new_jurisdictions"], "Jurisdiction `{0}` should be assigned to {1}".format(prods_1_jurisdiction, prods[1]))

		call =[ "push", "action", "--jurisdictions", "[{0}]".format(prods_0_jurisdiction), "beos.gateway", "issue", "[ \"{0}\", \"122.0000 BTS\", \"hello\" ]".format(prods[1]), "-p", "beos.gateway"]
		code, result = cluster.bios.make_cleos_call(call, False)
		log.info("{0}".format(result))

		trx_id = get_transaction_id_from_result(code, result)
		log.info("Waiting for transaction id: {} in block".format(trx_id))
		block = cluster.bios.wait_for_transaction_in_block(trx_id)

		call = ["get", "block", "{0}".format(block)]
		code, result = cluster.bios.make_cleos_call(call)
		log.info(result)
		result = json.loads(result)

		summary.equal(True, result["producer"] == "{0}".format(prods[0]), "This transaction should be signed by producer {0}".format(prods[0]))

		call = ["get", "producer_jurisdiction_for_block", "{0}".format(prods[0]), "{0}".format(block)]
		code, result = cluster.bios.make_cleos_call(call)
		log.info(result)
		result = json.loads(result)
		summary.equal(True, prods_0_jurisdiction in result["producer_jurisdiction_for_block"][0]["new_jurisdictions"], "Jurisdiction `{0}` should be assigned to {1}".format(prods_0_jurisdiction,prods[0]))

	except Exception as _ex:
		log.exception(_ex)
		summary.equal(True, False, "There should be no exceptions.")
	finally:
		status = summary.summarize()
		cluster.stop_all()
		exit(status)