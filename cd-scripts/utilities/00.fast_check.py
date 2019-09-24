#!/usr/bin/python3

# Simpler and more convenient simulation of `python3 011_[7.2]_updateprod_and_transaction_during_other_producer_turn_test.py`
# first usage:	python3 00.fast_check.py ~/src/13.BEOS/beos-core/build_release/programs/cleos/cleos 1
# next usages:	python3 00.fast_check.py ~/src/13.BEOS/beos-core/build_release/programs/cleos/cleos 0

import json
import time
import sys
import ctk

def exist_transaction( trx: str ):
	return len(trx) != 0

if __name__ == "__main__":
	
	try:

		INIT = sys.argv[2]

		print( "===================START===================" )

		bank = "beos.gateway"

		if int(INIT) != 0 :
			print( "**Issue**" )
			ctk.issue( bank, "100000.0000 BTS" )

			print( "**Adding jurisdictions**" )
			ctk.add_jurisdiction( "eosio", "argentina", 50 )
			ctk.add_jurisdiction( "eosio", "bolivia", 51 )
			ctk.add_jurisdiction( "eosio", "czech", 2000 )
			ctk.add_jurisdiction( "eosio", "denmark", 2001 )

			print( "**Waiting**" )
			ctk.wait_n_blocks(2)

		print( "**Updating producers**" )
		ctk.update_producers("beos.proda",[50])
		ctk.update_producers("beos.prodb",[51])

		print( "**Waiting**" )
		ctk.wait_n_blocks(4)

		prodb = 0
		print( "**Choosing proper producer**" )
		while True:
			ret = ctk.get_info()
			print( ret["head_block_producer"] )
			if ret["head_block_producer"] == "beos.proda" and prodb > 0:
				break
			if ret["head_block_producer"] == "beos.prodb":
				prodb += 1
			time.sleep(0.5)

		print( "**Update producer: beos.prodb**" )
		trx_id_up_01 = json.loads( ctk.update_producers("beos.prodb",[2000],[51]) )[ "trx_id" ]
		print( "** {} **".format( trx_id_up_01 ) )

		print( "**Transfer to : beos.proda**" )
		trx_id_01 = json.loads( ctk.transfer( bank, "beos.proda", "0.0001 BTS", [2000] ) )[ "trx_id" ]
		print( "** {} **".format( trx_id_01 ) )

		print( "**Update producer: beos.prodb**" )
		trx_id_up_02 = json.loads( ctk.update_producers("beos.prodb",[2001],[2000]) )[ "trx_id" ]
		print( "** {} **".format( trx_id_up_02 ) )

		print( "**Transfer to : beos.prodb**" )
		trx_id_02 = json.loads( ctk.transfer( bank, "beos.prodb", "0.0001 BTS", [2001] ) )[ "trx_id" ]
		print( "** {} **".format( trx_id_02 ) )

		print( "****Blocks generating****")
		for i in range( 100 ):
			print( ctk.get_info()["head_block_num"], " - " , ctk.get_info()["head_block_producer"], " - ", ctk.get_producer_jurisdiction( "beos.prodb" ) )

			if exist_transaction( ctk.get_transaction( trx_id_02 ) ):
				print("Transaction {} exists".format(trx_id_02) )
				break
			time.sleep(0.5)
			print( "****" )

		print( "===================END===================" )

	except Exception as _ex:
		print( "Exception `{0}` occures while executing".format( str(_ex) ) )
	finally:
		exit(0)
