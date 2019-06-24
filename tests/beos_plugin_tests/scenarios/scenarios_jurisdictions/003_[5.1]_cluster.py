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
		cluster, summary, args, log = init_cluster(__file__, 3, 3)
		cluster.run_all()
		code, mess = cluster.bios.make_cleos_call(["get", "info"])
		print("Bios: code: {0}, mess {1}\n".format(code, mess))
		for node in cluster.nodes:
			code, mess = node.make_cleos_call(["get", "info"])
			print("Nodes: code: {0}, mess {1}\n".format(code, mess))
		time.sleep(10)

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "0", "POLAND", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "1", "GERMANY", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")

		call = ["push", "action", "eosio", "addjurisdict", '[ "eosio", "2", "RUSSIA", "EAST EUROPE" ]', "-p", "eosio"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")

		call = ["push", "action", "eosio", "updateprod", '{"data":{"producer":"aaaaaaaaaaaa", "jurisdictions":[1]} }', "-p", "aaaaaaaaaaaa"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")

		call = ["push", "action", "eosio", "updateprod", '{"data":{"producer":"baaaaaaaaaaa", "jurisdictions":[2]} }', "-p", "baaaaaaaaaaa"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")

		call = ["push", "action", "eosio", "updateprod", '{"data":{"producer":"caaaaaaaaaaa", "jurisdictions":[1,2]} }', "-p", "caaaaaaaaaaa"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")


		call =[ "push", "action", "--jurisdictions", "[1]", "beos.gateway", "issue", "[ \"aaaaaaaaaaaa\", \"100.0000 BTS\", \"hello\" ]", "-p", "beos.gateway"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")
		call =[ "push", "action", "--jurisdictions", "[2]", "beos.gateway", "issue", "[ \"baaaaaaaaaaa\", \"100.0000 BTS\", \"hello\" ]", "-p", "beos.gateway"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")
		call =[ "push", "action", "--jurisdictions", "[1,2]","beos.gateway", "issue", "[ \"caaaaaaaaaaa\", \"100.0000 BTS\", \"hello\" ]", "-p", "beos.gateway"]
		code, result = cluster.bios.make_cleos_call(call)
		print(f"{result}")

		cluster.stop_all()
		
		#cluster.bios.stop_node()
	except Exception as _ex:
		pass
	finally:
		exit(0)