#!/usr/bin/python3

import subprocess
import logging
import os
import time
import sys
import json
import datetime

import eosio_tools

try:
    import config
except Exception as ex:
    msg = "config.py is not present. Please make a copy of config-example.py and name it as config.py. Edit config.py to customize your build environment."
    print(msg)

MODULE_NAME = "EOSIO Actions Py"
logger = logging.getLogger(MODULE_NAME)
logger.setLevel(config.LOG_LEVEL)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(config.LOG_LEVEL)
ch.setFormatter(logging.Formatter(config.LOG_FORMAT))

fh = logging.FileHandler(config.MAIN_LOG_PATH)
fh.setLevel(config.LOG_LEVEL)
fh.setFormatter(logging.Formatter(config.LOG_FORMAT))

logger.addHandler(ch)
logger.addHandler(fh)

def unlock_wallet(wallet_name, wallet_password):
    parameters = [
        config.CLEOS_EXECUTABLE, 
        "--print-request",
        "--print-response",
        "wallet", "unlock", 
        "-n", wallet_name, 
        "--password", wallet_password
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    eosio_tools.run_command(parameters)

def import_key(wallet_name, key, wallet_url = None):
    if key:
        parameters = [
            config.CLEOS_EXECUTABLE,
        ]
        
        if config.LOG_LEVEL == logging.DEBUG:
            parameters = parameters + [
                "--print-request",
                "--print-response",
            ]

        if wallet_url is not None:
            parameters = parameters + [
                "--wallet-url", wallet_url,
            ]

        parameters = parameters + [
            "wallet", "import", 
            "-n", wallet_name, 
            "--private-key", key
        ]
        logger.info("Executing command: {0}".format(" ".join(parameters)))
        eosio_tools.run_command(parameters)
    else:
        eosio_tools.raiseEOSIOException("Importing empty key!")

def create_wallet(wallet_url = None, unlock = False):
    logger.info("*** Create wallet, wallet url {0}".format(wallet_url))

    parameters = [
        config.CLEOS_EXECUTABLE
    ]

    if config.LOG_LEVEL == logging.DEBUG:
        parameters = parameters + [
            "--print-request",
            "--print-response",
        ]

    if wallet_url is not None:
        parameters = parameters + [
            "--wallet-url", wallet_url
        ]

    parameters = parameters + [
        "wallet", "create", 
        "-n", config.MASTER_WALLET_NAME,
        "-f", config.WALLET_PASSWORD_PATH
    ]

    logger.info("Executing command: {0}".format(" ".join(parameters)))
    eosio_tools.run_command(parameters)

    if unlock:
        wallet_password = None
        with open(config.WALLET_PASSWORD_PATH, "r") as password_file:
            wallet_password = password_file.readline()
        unlock_wallet(config.MASTER_WALLET_NAME, wallet_password)

    for key in config.SYSTEM_ACCOUNT_KEYS:
        import_key(config.MASTER_WALLET_NAME, key, wallet_url)

def create_account(creator, name, owner_key, active_key, transfer_ram = False, schema = "http"):
    if not owner_key and not active_key:
        eosio_tools.raiseEOSIOException("Owner key or active key are empty, aborting")
    parameters = [
        config.CLEOS_EXECUTABLE
    ]
    
    if config.LOG_LEVEL == logging.DEBUG:
        parameters = parameters + [
            "--print-request",
            "--print-response",
        ]

    parameters = parameters + [
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "create", "account"
    ]
    if transfer_ram:
        parameters.append("--transfer-ram")
    parameters += [creator, name, owner_key, active_key, "--json"]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    ret = json.loads(eosio_tools.run_command_and_return_output(parameters))
    logger.debug(ret)
    transaction_id = ret.get("transaction_id", None)
    if transaction_id is not None:
        target_block_num = ret["processed"]["block_num"]
        block_until_transaction_in_block(transaction_id, target_block_num)
    else:
        eosio_tools.raiseEOSIOException("No transaction_id in response")

def set_contract(account, contract, permission, schema = "http"):
    parameters = [
        config.CLEOS_EXECUTABLE
    ]
    
    if config.LOG_LEVEL == logging.DEBUG:
        parameters = parameters + [
            "--print-request",
            "--print-response",
        ]

    parameters = parameters + [
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "set", "contract", account, contract, "-p", permission, "--json"
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    ret = json.loads(eosio_tools.run_command_and_return_output(parameters))
    logger.debug(ret)
    transaction_id = ret.get("transaction_id", None)
    if transaction_id is not None:
        target_block_num = ret["processed"]["block_num"]
        block_until_transaction_in_block(transaction_id, target_block_num)
    else:
        eosio_tools.raiseEOSIOException("No transaction_id in response")

def push_action(account, action, data, permission, schema = "http"):
    parameters = [
        config.CLEOS_EXECUTABLE
    ]
    
    if config.LOG_LEVEL == logging.DEBUG:
        parameters = parameters + [
            "--print-request",
            "--print-response",
        ]

    parameters = parameters + [
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "push", "action", account, action, data, "-p", permission, "--json"
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    ret = json.loads(eosio_tools.run_command_and_return_output(parameters))
    logger.debug(ret)
    transaction_id = ret.get("transaction_id", None)
    if transaction_id is not None:
        target_block_num = ret["processed"]["block_num"]
        block_until_transaction_in_block(transaction_id, target_block_num)
    else:
        eosio_tools.raiseEOSIOException("No transaction_id in response")

def get_balance(_account_name, _currency, schema = "http"):
    parameters = [
        config.CLEOS_EXECUTABLE
    ]
    
    if config.LOG_LEVEL == logging.DEBUG:
        parameters = parameters + [
            "--print-request",
            "--print-response",
        ]

    parameters = parameters + [
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "get", "currency", "balance", "eosio.token", _account_name, _currency
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    return float(eosio_tools.run_command_and_return_output(parameters).decode('utf-8').split()[0])

def get_account(_account_name, schema = "http"):
    parameters = [
        config.CLEOS_EXECUTABLE, 
    ]
    
    if config.LOG_LEVEL == logging.DEBUG:
        parameters = parameters + [
            "--print-request",
            "--print-response",
        ]

    parameters = parameters + [
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "get", "account", "-j", _account_name
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    logger.info(json.dumps(json.loads(eosio_tools.run_command_and_return_output(parameters)),indent=2,separators=(',', ': ')))

BLOCK_TYPE_HEADBLOCK = "head_block_num"
BLOCK_TYPE_IRREVERSIBLE = "last_irreversible_block_num"
def block_until_transaction_in_block(transaction_id, block_num, block_type = BLOCK_TYPE_HEADBLOCK, timeout = 60.):
    import eosio_rpc_client
    EOSIO = eosio_rpc_client.EosioInterface(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT)
    logger.info("Block until transaction_id: {0} is in block {1}".format(transaction_id, block_num))
    import time
    step = 0.25
    timeout_cnt = 0.
    while True:
        last_block_num = EOSIO.chain.get_info()[BLOCK_TYPE_HEADBLOCK]
        logger.debug("Waiting for block: {0}, current block is {1}".format(block_num, last_block_num))
        if last_block_num >= block_num:
            logger.debug("Scanning block: {0}".format(last_block_num))
            get_block_data = {"block_num_or_id" : block_num}
            get_block_resp = EOSIO.chain.get_block(get_block_data)
            for transaction in get_block_resp["transactions"]:
                status = transaction.get("status", None)
                trx = transaction.get("trx", None)
                if trx is not None and status == "executed":
                    tid = trx.get("id", None)
                    if tid is not None and tid == transaction_id:
                        logger.info("Transaction id: {0} found in block: {1}".format(transaction_id, block_num))
                        return
            logger.info("Transaction id: {0} not found in block: {1}".format(transaction_id, block_num))
        time.sleep(step)
        timeout_cnt = timeout_cnt + step
        if timeout_cnt > timeout:
            msg = "Timeout reached during block_until_transaction_in_block"
            logger.error(msg)
            raise TimeoutError(msg)
