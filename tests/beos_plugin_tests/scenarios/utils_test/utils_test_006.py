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

		rpc = node.get_url_caller()
		start = node.run_node()

		head_block_num_pre = rpc.chain.get_info()["head_block_num"]
		node.wait_till_block(head_block_num_pre + 5)
		head_block_num_post = rpc.chain.get_info()["head_block_num"]
		summary.equal(True, head_block_num_post >= head_block_num_pre + 5, "head_block_num_post >= head_block_num_pre + 5" )

		head_block_num_pre = rpc.chain.get_info()["head_block_num"]
		node.wait_n_blocks(5)
		head_block_num_post = rpc.chain.get_info()["head_block_num"]
		summary.equal(True, head_block_num_post >= head_block_num_pre + 5, "head_block_num_post >= head_block_num_pre + 5" )

	except Exception as _ex:
		log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
	finally:
		summary_status = summary.summarize()
		node.stop_node()
		exit(summary_status)