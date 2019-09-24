#!/usr/bin/python3

'''

CTK - Cleos ToolKit

Simple tool that allows to simply implement scenarios, that require block (half second) precision
This toolkit has some basic functions, that gives you basics utility, and grant you UX same as cleos

To use it from console, forst make sure, that keosd and nodes is running, and wallet is unlocked, then just type:

python3 - $PATH_TO_CLEOS

#when python shell statup type:
import ctk

#if everything is setted up, get info should be displayed
#if something goes wrong, you can change path to cleos by:

ctk.CLEOS = NEW_PATH_TO_CLEOS

#if you want to generate bash script, which allows you to run this script independly from python you have to:
#	At the beginning:

ctk.bash_generation_initialization(PATH_TO_BASH_SCRIPT)

#	If you want to add something to script, you can use this methode:

cth.bash_generation_write_line(BASH_COMMAND)

#	At the end:

cth.bash_generation_finalization()

#so the file will be properly closed

'''

import os
import json
import sys
import time
import random

CLEOS = sys.argv[1]
GENERATE_BASH = None

def bash_generation_initialization(abs_path_to_file : str = "/tmp/script.bash"):
	global GENERATE_BASH
	if (GENERATE_BASH is not None):
		bash_generation_finalization()
	GENERATE_BASH = open(abs_path_to_file, "w")
	bash_generation_write_line("#!/bin/bash")

def bash_generation_write_line(line : str):
	global GENERATE_BASH
	if (GENERATE_BASH is not None) and (GENERATE_BASH.writable()):
		GENERATE_BASH.write("{}\n".format(line))

def bash_generation_finalization():
	global GENERATE_BASH
	if GENERATE_BASH is not None:
		GENERATE_BASH.close()
		GENERATE_BASH = None

def cleos(args : list):
	bash_generation_write_line(CLEOS + " " + " ".join(args))
	return os.popen(CLEOS + " " + " ".join(args)).read()

def push_action(contract_owner : str, trx_name : str, data : str, permissions : list, execute_on : list = None, force_uniq : bool = False, __exec = True):
	query = ["push", "action"]
	if force_uniq:
		query.append("-f")
	if execute_on:
		query.append("-u")
		query.append("'{}'".format(execute_on))
	query.extend([contract_owner, trx_name])
	query.extend(["'{}'".format(data)])
	query.extend(["-j", "-p"])
	query.extend(permissions)
	if __exec:
		return cleos(query)
	else:
		query

def get_info():
	return json.loads(cleos(["get", "info"]))

def get_current_block():
	return int(get_info()["head_block_num"])

def wait_n_blocks(num : int = 1):
	bash_generation_write_line("sleep {}".format(0.5 * num))
	time.sleep(0.5 * num)

def wait_till_block(num : int):
	iterations = 0
	while get_current_block() < num:
		time.sleep(0.1)
		iterations += 1
	bash_generation_write_line("sleep {}".format(0.1 * iterations))

def get_next_irrevesible_block():
	amount_of_prods = len(get_active_producers())
	return (int(amount_of_prods * 12) if amount_of_prods > 1 else 1) + int(get_info()["last_irreversible_block_num"])

def get_active_producers():
	list_of_prods = list()
	result = json.loads(cleos(["get", "schedule", "-j"]))["active"]["producers"]
	for var in result:
		list_of_prods.append(var["producer_name"])
	return list_of_prods	

def issue(to : str, amount: str, execute_on : list = None, force_uniq = False):
	data = str('[ "' + to + '", "' + amount +'", "nice money" ]')
	return push_action("eosio.token", "issue", data, [ "beos.gateway" ], execute_on, force_uniq)

def transfer( _from : str, to : list, amount : str, execute_on : list = None, force_uniq = False):
	data = str('[ "' + _from + '", "' + to + '", "' + amount + '", "HI" ]')
	return push_action("eosio.token", "transfer", data, [ _from ], execute_on, force_uniq)

def update_producers(prod : str, new_jurs : list, execute_on : list = None, force_uniq = False):
	data = str('{"data":{"producer":'+prod+', "jurisdictions":'+str(new_jurs)+'}}')
	return push_action("eosio", "updateprod", data, [ prod ], execute_on, force_uniq)

def add_jurisdiction(prod : str, name : str, code : int, desc : str = "sample description", execute_on : list = None, force_uniq = False):
	data = '[ "{}", {}, "{}", "{}" ]'.format(prod, code, name, desc)
	return push_action("eosio", "addjurisdict", data, [ prod ], execute_on, force_uniq)

def get_all_jurisdictions():
	return json.loads(cleos(["get", "all_jurisdictions"]))["jurisdictions"]

def get_producer_jurisdiction( producer : str ):
	return json.loads(cleos(["get", "producer_jurisdiction", "'[\"" + producer + "\"]'" ]))

def get_transaction( trx : str ):
	return cleos( ["get", "transaction", "\"" + trx + "\"" ] )

def get_all_keys():
	return json.loads(cleos(["wallet", "keys"]))

def get_all_users():
	result = dict()
	keys = get_all_keys()
	for key in keys:
		accounts = json.loads(cleos(["get", "accounts", key]))["account_names"]
		for acc in accounts:
			result[acc] = 1
	return list(result.keys())
	
def get_currency_balance(user : str):
	txt = cleos(["get", "currency", "balance", "eosio.token", user])
	txt = txt.splitlines()
	result = dict()
	for line in txt:
		tmp = line.split()
		assert len(tmp) >= 2
		result[tmp[1]] = tmp[0]
	return result

def create_account(name : str, creator : str = "beos.gateway", own_key : str = None, act_key = None, __transfer_ram : bool = True, execute_on : list = None, force_uniq = False):
	query = [ "create", "account", creator, name ]
	keys = get_all_keys()
	rnd_idx = random.randint(0, len(keys)-1)
	if own_key:
		query.append(own_key)
	else:
		query.append(keys[rnd_idx])
	if act_key:
		query.append(act_key)
	else:
		query.append(keys[rnd_idx])
	if __transfer_ram:
		query.append("--transfer-ram")
	if force_uniq:
		query.append("-f")
	if execute_on:
		query.append("-u")
		query.append("'{}'".format(execute_on))
	return cleos(query)

def get_account(user : str, __simpify = True):
	txt = json.loads(cleos(["get", "account", user, "-j"]))
	if not __simpify:
		return txt
	result = dict()
	result["CPU"] = float(txt["total_resources"]["cpu_weight"].split(" ")[0])
	result["NET"] = float(txt["total_resources"]["net_weight"].split(" ")[0])
	result["RAM"] = int(txt["total_resources"]["ram_bytes"])
	if "core_liquid_balance" in txt:
		result["LIQ"] = float(txt["core_liquid_balance"].split(" ")[0])
	else:
		result["LIQ"] = 0.0
	return result

print(get_info())
