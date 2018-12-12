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
        "wallet", "unlock", 
        "-n", wallet_name, 
        "--password", wallet_password
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    eosio_tools.run_command(parameters)

def import_key(wallet_name, key, wallet_url = None):
    if key:
        parameters = [
            config.CLEOS_EXECUTABLE
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

def create_account(creator, name, owner_key, active_key, schema = "http"):
    if not owner_key and not active_key:
        logger.error("Owner key or active key are empty, aborting")
        raise eosio_tools.EOSIOException("Owner key or active key are empty, aborting")
    parameters = [
        config.CLEOS_EXECUTABLE, 
        "--print-request",
        "--print-response",
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "create", "account", creator, name, owner_key, active_key
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    eosio_tools.run_command(parameters)

def set_contract(account, contract, permission, schema = "http"):
    parameters = [
        config.CLEOS_EXECUTABLE, 
        "--print-request",
        "--print-response",
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "set", "contract", account, contract, "-p", permission
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    eosio_tools.run_command(parameters)

def push_action(account, action, data, permission, schema = "http"):
    parameters = [
        config.CLEOS_EXECUTABLE, 
        "--print-request",
        "--print-response",
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "push", "action", account, action, data, "-p", permission
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    eosio_tools.run_command(parameters)

def get_balance(_account_name, _currency, schema = "http"):
    parameters = [
        config.CLEOS_EXECUTABLE, 
        "--print-request",
        "--print-response",
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "get", "currency", "balance", "eosio.token", _account_name, _currency
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    return float(eosio_tools.run_command_and_return_output(parameters).decode('utf-8').split()[0])

def get_account(_account_name, schema = "http"):
    parameters = [
        config.CLEOS_EXECUTABLE, 
        "--print-request",
        "--print-response",
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "get", "account", "-j", _account_name
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    logger.info(json.dumps(json.loads(eosio_tools.run_command_and_return_output(parameters)),indent=2,separators=(',', ': ')))
