#!/usr/bin/python3

import subprocess
import logging
import os
import time
import sys

try:
    import config
except Exception as ex:
    msg = "config.py is not present. Please make a copy of config-example.py and name it as config.py. Edit config.py to customize your build environment."
    print(msg)

MODULE_NAME = "EOSIO Py"
logger = logging.getLogger(MODULE_NAME)
logger.setLevel(config.LOG_LEVEL)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(config.LOG_LEVEL)
ch.setFormatter(logging.Formatter(config.LOG_FORMAT))

fh = logging.FileHandler(os.path.dirname(os.path.abspath(__file__)) + '/beos_deploy.log')
fh.setLevel(config.LOG_LEVEL)
fh.setFormatter(logging.Formatter(config.LOG_FORMAT))

logger.addHandler(ch)
logger.addHandler(fh)

class EOSIOException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

def show_wallet_unlock_postconf():
    wallet_password = None
    with open(config.WALLET_PASSWORD_PATH, "r") as password_file:
        wallet_password = password_file.readline()
        wallet_password = wallet_password[1:-1] # remove " character from begin and end of string

    parameters = [config.CLEOS_EXECUTABLE, 
        "wallet", "unlock", 
        "-n", config.MASTER_WALLET_NAME, 
        "--password", wallet_password
    ]
    logger.info("Dont forget to unlock your wallet with command: {0}".format(" ".join(parameters)))

def show_keosd_postconf(ip_address, port, wallet_dir, use_https = False):
    parameters = None
    if use_https:
        # run kleosd in https mode
        parameters = [config.KEOSD_EXECUTABLE,
            "--https-server-address","{0}:{1}".format(ip_address, port),
            "--https-certificate-chain-file", config.KEOSD_CERTIFICATE_CHAIN_FILE,
            "--https-private-key-file", config.KEOSD_PRIVATE_KEY_FILE,
            "--wallet-dir", wallet_dir,
        ]
    else:
        # run kleosd in http mode
        parameters = [config.KEOSD_EXECUTABLE,
            "--http-server-address","{0}:{1}".format(ip_address, port) ,
            "--wallet-dir", wallet_dir,
        ]
    logger.info("Configuration complete, you can now run keosd with command (consider running in screen): {0}".format(" ".join(parameters)))

def show_nodeos_postconf(node_index, name, public_key, use_https = False):
    working_dir = "{0}{1}-{2}/".format(config.NODEOS_WORKING_DIR, node_index, name)

    https_opts = [
        "--signature-provider", "{0}=KEOSD:http://{1}:{2}/v1/wallet/sign_digest".format(public_key, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "--http-server-address", "{0}:{1}".format(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    ]

    if use_https:
        https_opts = [
            "--signature-provider", "{0}=KEOSD:https://{1}:{2}/v1/wallet/sign_digest".format(public_key, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
            "--https-server-address", "{0}:{1}".format(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
            "--https-certificate-chain-file", config.KEOSD_CERTIFICATE_CHAIN_FILE,
            "--https-private-key-file", config.KEOSD_PRIVATE_KEY_FILE
        ]

    parameters = [
        config.NODEOS_EXECUTABLE,
        "--max-irreversible-block-age", "-1",
        "--contracts-console",
        "--blocks-dir", os.path.abspath(working_dir) + '/blocks',
        "--config-dir", os.path.abspath(working_dir),
        "--data-dir", os.path.abspath(working_dir),
        "--chain-state-db-size-mb", "1024",
        "--enable-stale-production",
        "--producer-name", name,
    ]

    plugins = [
        "--plugin", "eosio::http_plugin",
        "--plugin", "eosio::chain_api_plugin",
        "--plugin", "eosio::producer_plugin",
        "--plugin", "eosio::beos_plugin",
        "--plugin", "eosio::beos_api_plugin",
        "--plugin", "eosio::history_plugin",
        "--plugin", "eosio::history_api_plugin"
    ]

    parameters = parameters + https_opts + plugins
    logger.info("Configuration complete, you can now run nodeos with command (consider running in screen): {0}".format(" ".join(parameters)))

def run_keosd(ip_address, port, wallet_dir, use_https = False):
    logger.info("*** Running KLEOSD at {0}:{1} in {2}".format(ip_address, port, wallet_dir))
    from sys import exit
    if os.path.exists(config.DEFAULT_WALLET_DIR):
        logger.error("{0} exists. Please delete it manually and try again.".format(config.DEFAULT_WALLET_DIR))
        exit(1)
    
    if os.path.exists(config.WALLET_PASSWORD_DIR):
        logger.error("{0} exists. Please delete it manually and try again.".format(config.WALLET_PASSWORD_DIR))
        exit(1)
    
    os.makedirs(config.DEFAULT_WALLET_DIR)
    os.makedirs(config.WALLET_PASSWORD_DIR)

    time.sleep(0.5)

    parameters = None
    if use_https:
        # run kleosd in https mode
        parameters = [config.KEOSD_EXECUTABLE, 
            "--https-server-address","{0}:{1}".format(ip_address, port), 
            "--https-certificate-chain-file", config.KEOSD_CERTIFICATE_CHAIN_FILE, 
            "--https-private-key-file", config.KEOSD_PRIVATE_KEY_FILE, 
            "--wallet-dir", wallet_dir,
        ]
    else:
        # run kleosd in http mode
        parameters = [config.KEOSD_EXECUTABLE, 
            "--http-server-address","{0}:{1}".format(ip_address, port) ,
            "--wallet-dir", wallet_dir,
        ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    subprocess.Popen(parameters, stdout=config.log_main, stderr=config.log_error)
    time.sleep(1.0)

def unlock_wallet(wallet_name, wallet_password):
    parameters = [config.CLEOS_EXECUTABLE, 
        "wallet", "unlock", 
        "-n", wallet_name, 
        "--password", wallet_password
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    subprocess.run(parameters, stdout=config.log_main, stderr=config.log_error)

def import_key(wallet_name, key, wallet_url = None):
    if key:
        parameters = [config.CLEOS_EXECUTABLE, 
            "wallet", "import", 
            "-n", wallet_name, 
            "--private-key", key
        ]
        if wallet_url is not None:
            parameters = [config.CLEOS_EXECUTABLE, 
            "--wallet-url", wallet_url,
            "wallet", "import", 
            "-n", wallet_name, 
            "--private-key", key
        ]
        
        logger.info("Executing command: {0}".format(" ".join(parameters)))
        subprocess.run(parameters, stdout=config.log_main, stderr=config.log_error)
    else:
        logger.error("Importing empty key!")
        raise EOSIOException("Importing empty key!")

def create_wallet(wallet_url = None, unlock = False):
    logger.info("*** Create wallet, wallet url {0}".format(wallet_url))

    # if wallet_url is empty run local wallet
    parameters = [config.CLEOS_EXECUTABLE, 
        "wallet", "create", 
        "-n", config.MASTER_WALLET_NAME, 
        "-f", config.WALLET_PASSWORD_PATH
    ]
    if wallet_url is not None:
        parameters = [config.CLEOS_EXECUTABLE, 
            "--wallet-url", wallet_url,
            "wallet", "create", 
            "-n", config.MASTER_WALLET_NAME,
            "-f", config.WALLET_PASSWORD_PATH
        ]

    logger.info("Executing command: {0}".format(" ".join(parameters)))
    subprocess.run(parameters, stdout=config.log_main, stderr=config.log_error)

    if unlock:
        wallet_password = None
        with open(config.WALLET_PASSWORD_PATH, "r") as password_file:
            wallet_password = password_file.readline()
            wallet_password = wallet_password[1:-1] # remove " character from begin and end of string
        unlock_wallet(config.MASTER_WALLET_NAME, wallet_password)

    for key in config.SYSTEM_ACCOUNT_KEYS:
        import_key(config.MASTER_WALLET_NAME, key, wallet_url)

def run_nodeos(node_index, name, public_key, use_https = False):
    if not public_key:
        logger.error("Public key is empty, aborting")
        raise EOSIOException("Public key is empty, aborting")
    from shutil import rmtree, copy
    working_dir = "{0}{1}-{2}/".format(config.NODEOS_WORKING_DIR, node_index, name)

    logger.info("*** START NODE in {0}".format(working_dir))

    if os.path.exists(working_dir):
        rmtree(working_dir)
    os.makedirs(working_dir)
    copy(config.GENESIS_JSON_FILE_SRC, working_dir + config.GENESIS_JSON_FILE)

    https_opts = [
        "--signature-provider", "{0}=KEOSD:http://{1}:{2}/v1/wallet/sign_digest".format(public_key, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "--http-server-address", "{0}:{1}".format(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    ]

    if use_https:
        https_opts = [
            "--signature-provider", "{0}=KEOSD:https://{1}:{2}/v1/wallet/sign_digest".format(public_key, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
            "--https-server-address", "{0}:{1}".format(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
            "--https-certificate-chain-file", config.KEOSD_CERTIFICATE_CHAIN_FILE, 
            "--https-private-key-file", config.KEOSD_PRIVATE_KEY_FILE
        ]

    parameters = [
        config.NODEOS_EXECUTABLE,
        "--max-irreversible-block-age", "-1",
        "--contracts-console",
        "--genesis-json", os.path.abspath(working_dir + config.GENESIS_JSON_FILE),
        "--blocks-dir", os.path.abspath(working_dir) + '/blocks',
        "--config-dir", os.path.abspath(working_dir),
        "--data-dir", os.path.abspath(working_dir),
        "--chain-state-db-size-mb", "1024",
        "--enable-stale-production",
        "--producer-name", name,
    ] 
    
    plugins = [
        "--plugin", "eosio::http_plugin",
        "--plugin", "eosio::chain_api_plugin",
        "--plugin", "eosio::producer_plugin",
        "--plugin", "eosio::beos_plugin",
        "--plugin", "eosio::beos_api_plugin",
        "--plugin", "eosio::history_plugin",
        "--plugin", "eosio::history_api_plugin"
    ]

    parameters = parameters + https_opts + plugins

    logger.info("Executing command: {0}".format(" ".join(parameters)))
    try:
        import time
        subprocess.Popen(parameters, stdout=config.log_main, stderr=config.log_error)
        time.sleep(1.5)
    except Exception as ex:
        logger.error("Exception during spawning nodeos process: {0}".format(ex))
    return 0

def create_account(creator, name, owner_key, active_key, schema = "http"):
    if not owner_key and not active_key:
        logger.error("Owner key or active key are empty, aborting")
        raise EOSIOException("Owner key or active key are empty, aborting")
    parameters = [config.CLEOS_EXECUTABLE, 
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "create", "account", creator, name, owner_key, active_key]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    ret = subprocess.run(parameters, stdout=config.log_main, stderr=config.log_error)
    retcode = ret.returncode
    time.sleep(1)
    logger.info("Executed with ret: {0}".format(ret))
    if retcode != 0:
        logger.error("Initialization failed on last command")
        raise EOSIOException("Initialization failed on last command")

def set_contract(account, contract, permission, schema = "http"):
    parameters = [config.CLEOS_EXECUTABLE, 
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "set", "contract", account, contract, "-p", permission]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    ret = subprocess.run(parameters, stdout=config.log_main, stderr=config.log_error)
    retcode = ret.returncode
    time.sleep(1)
    logger.info("Executed with ret: {0}".format(ret))
    if retcode != 0:
        logger.error("Initialization failed on last command")
        raise EOSIOException("Initialization failed on last command")

def push_action(account, action, data, permission, schema = "http"):
    parameters = [config.CLEOS_EXECUTABLE, 
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "push", "action", account, action, data, "-p", permission]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    ret = subprocess.run(parameters, stdout=config.log_main, stderr=config.log_error)
    retcode = ret.returncode
    time.sleep(1)
    logger.info("Executed with ret: {0}".format(ret))
    if retcode != 0:
        logger.error("Initialization failed on last command")
        raise EOSIOException("Initialization failed on last command")

def terminate_running_tasks():
    parameters = ["pkill", "nodeos"]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    ret = subprocess.run(parameters, stdout=config.log_main, stderr=config.log_error)
    time.sleep(1)
    logger.info("Executed with ret: {0}".format(ret))

    parameters = ["pkill", "keosd"]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    ret = subprocess.run(parameters, stdout=config.log_main, stderr=config.log_error)
    time.sleep(1)
    logger.info("Executed with ret: {0}".format(ret))

if __name__ == '__main__':
    run_keosd(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT, config.DEFAULT_WALLET_DIR)
    create_wallet("http://{0}:{1}".format(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT))
    run_nodeos(0, "eosio", config.EOSIO_PUBLIC_KEY)
