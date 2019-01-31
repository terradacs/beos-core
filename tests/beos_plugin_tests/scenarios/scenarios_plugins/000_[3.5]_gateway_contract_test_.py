#!/usr/bin/python3

# Scenario based on test : [2.5]-Vote-test

import os
import sys
import time
import datetime 

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult
from beos_test_utils.utility_misc import *

def check_gateway_table( node ):

	scope = "beos.gateway"
	code = "beos.gateway"
	table = "gatewaystate"
	json = "true"

	cnt = 0
	asset_patterns = [ "PXBTS", "PXBRNP", "PXEOS" ]

	rpc = node.get_url_caller()
	data = {"scope":scope, "code":code, "table":table, "json": json}

	rpc_result = rpc.chain.get_table_rows( data )
	if rpc_result == None:
		return 0

	for row in rpc_result["rows"]:
		for asset in row["proxy_assets"]:
			item = asset["proxy_asset"]
			elements = item.split(" ")
			for pattern in asset_patterns:
				if pattern == elements[ len( elements ) - 1 ]:
					cnt += 1

	return cnt

if __name__ == "__main__":
	try:
		node, summary, args, log = init(__file__)

		node.run_node()

		rpc_nr_assets = check_gateway_table( node )

		what = "Incorrect number of assets: rpc: %s should be: %s \n" % ( rpc_nr_assets, 3 )
		summary.equal( rpc_nr_assets, 3, what )

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)