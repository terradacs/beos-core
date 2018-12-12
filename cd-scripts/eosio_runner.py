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

MODULE_NAME = "EOSIO Runner Py"
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

def show_wallet_unlock_postconf():
    wallet_password = None
    with open(config.WALLET_PASSWORD_PATH, "r") as password_file:
        wallet_password = password_file.readline()
        #wallet_password = wallet_password[1:-1] # remove " character from begin and end of string

    parameters = [
        config.CLEOS_EXECUTABLE, 
        "wallet", "unlock", 
        "-n", config.MASTER_WALLET_NAME, 
        "--password", wallet_password
    ]
    logger.info("Dont forget to unlock your wallet with command: {0}".format(" ".join(parameters)))

def show_keosd_postconf(ip_address, port, wallet_dir, use_https = False):
    parameters = [config.KEOSD_EXECUTABLE,
        "--http-server-address","{0}:{1}".format(ip_address, port) ,
        "--wallet-dir", wallet_dir,
    ]
    if use_https:
        # run kleosd in https mode
        parameters = [
            config.KEOSD_EXECUTABLE,
            "--https-server-address","{0}:{1}".format(ip_address, port),
            "--https-certificate-chain-file", config.KEOSD_CERTIFICATE_CHAIN_FILE,
            "--https-private-key-file", config.KEOSD_PRIVATE_KEY_FILE,
            "--wallet-dir", wallet_dir,
        ]
    logger.info("Configuration complete, you can now run keosd with command (consider running in screen): {0}".format(" ".join(parameters)))

def show_nodeos_postconf(node_index, name, public_key, use_https = False):
    working_dir = "{0}{1}-{2}/".format(config.NODEOS_WORKING_DIR, node_index, name)

    parameters = [
        config.NODEOS_EXECUTABLE,
        "--contracts-console",
        "--blocks-dir", os.path.abspath(working_dir) + '/blocks',
        "--config-dir", os.path.abspath(working_dir),
        "--data-dir", os.path.abspath(working_dir),
    ]

    logger.info("Configuration complete, you can now run nodeos with command (consider running in screen): {0}".format(" ".join(parameters)))

def run_keosd(ip_address, port, wallet_dir, use_https = False, forceWalletCleanup = False):
    from sys import exit
    logger.info("*** Running KLEOSD at {0}:{1} in {2}".format(ip_address, port, wallet_dir))
    eosio_tools.detect_process_by_name("keosd", ip_address, port)
    
    from shutil import rmtree, move
    if os.path.exists(config.DEFAULT_WALLET_DIR):
        if forceWalletCleanup:
            rmtree(config.DEFAULT_WALLET_DIR)
        else:
            logger.error("{0} exists. Please delete it manually and try again.".format(config.DEFAULT_WALLET_DIR))
            exit(1)
    
    if os.path.exists(config.WALLET_PASSWORD_DIR):
        if forceWalletCleanup:
            rmtree(config.WALLET_PASSWORD_DIR)
        else:
            logger.error("{0} exists. Please delete it manually and try again.".format(config.WALLET_PASSWORD_DIR))
            exit(1)
    
    os.makedirs(config.DEFAULT_WALLET_DIR)
    os.makedirs(config.WALLET_PASSWORD_DIR)

    log_file_name = eosio_tools.get_log_file_name("keosd")
    if os.path.exists(log_file_name):
        move(log_file_name, log_file_name + ".old")

    parameters = [
        config.KEOSD_EXECUTABLE,
        "--http-server-address","{0}:{1}".format(ip_address, port) ,
        "--wallet-dir", wallet_dir,
    ]
    if use_https:
        # run kleosd in https mode
        parameters = [
            config.KEOSD_EXECUTABLE,
            "--https-server-address","{0}:{1}".format(ip_address, port),
            "--https-certificate-chain-file", config.KEOSD_CERTIFICATE_CHAIN_FILE,
            "--https-private-key-file", config.KEOSD_PRIVATE_KEY_FILE,
            "--wallet-dir", wallet_dir,
        ]

    eosio_tools.save_screen_cfg("./keosd_screen.cfg", log_file_name)
    screen_params = [
        "screen",
        "-m",
        "-d",
        "-L",
        "-c",
        "./keosd_screen.cfg",
        "-S",
        eosio_tools.get_screen_name("keosd")
    ]

    parameters = screen_params + parameters
    logger.info("Running keosd with command: {0}".format(" ".join(parameters)))
    try:
        subprocess.Popen(parameters)
        eosio_tools.save_pid_file("./run_keosd.pid", "keosd")
        eosio_tools.wait_for_string_in_file(log_file_name, "add api url: /v1/wallet/unlock", 10.)
    except Exception as ex:
        logger.error("Exception during keosd run: {0}".format(ex))
        eosio_tools.kill_process("./run_keosd.pid", "keosd", ip_address, port)
        sys.exit(1)

def run_nodeos(node_index, name, public_key, use_https = False):
    eosio_tools.detect_process_by_name("nodeos", config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    if not public_key:
        eosio_tools.raiseEOSIOException("Public key is empty, aborting")
    from shutil import rmtree, copy, move
    working_dir = "{0}{1}-{2}/".format(config.NODEOS_WORKING_DIR, node_index, name)

    logger.info("*** START NODE in {0}".format(working_dir))

    if os.path.exists(working_dir):
        rmtree(working_dir)
    os.makedirs(working_dir)
    logger.info("Copying genesis file from {0} to {1}".format(config.GENESIS_JSON_FILE_SRC, working_dir + config.GENESIS_JSON_FILE))
    if os.path.exists(config.GENESIS_JSON_FILE_SRC):
        copy(config.GENESIS_JSON_FILE_SRC, working_dir + config.GENESIS_JSON_FILE)
    else:
        eosio_tools.raiseEOSIOException("File {0} does not exists.".format(config.GENESIS_JSON_FILE_SRC))
        
    logger.info("Copying config file from {0} to {1}".format(config.BEOS_CONFIG_FILE_SRC, working_dir + config.BEOS_CONFIG_FILE))
    if os.path.exists(config.BEOS_CONFIG_FILE_SRC):
        copy(config.BEOS_CONFIG_FILE_SRC, working_dir + config.BEOS_CONFIG_FILE)
    else:
        eosio_tools.raiseEOSIOException("File {0} does not exists.".format(config.BEOS_CONFIG_FILE_SRC))

    log_file_name = eosio_tools.get_log_file_name("nodeos")
    if os.path.exists(log_file_name):
        move(log_file_name, log_file_name + ".old")

    parameters = [
        config.NODEOS_EXECUTABLE,
        "--contracts-console",
        "--genesis-json", os.path.abspath(working_dir + config.GENESIS_JSON_FILE),
        "--blocks-dir", os.path.abspath(working_dir) + '/blocks',
        "--config-dir", os.path.abspath(working_dir),
        "--data-dir", os.path.abspath(working_dir),
    ]

    eosio_tools.save_screen_cfg("./nodeos_screen.cfg", log_file_name)
    screen_params = [
        "screen",
        "-m",
        "-d",
        "-L",
        "-c",
        "./nodeos_screen.cfg",
        "-S",
        eosio_tools.get_screen_name("nodeos")
    ]

    parameters = screen_params + parameters
    logger.info("Running nodeos with command: {0}".format(" ".join(parameters)))
    try:
        subprocess.Popen(parameters)
        eosio_tools.save_pid_file("./run_nodeos.pid", "nodeos")
        eosio_tools.wait_for_blocks_produced(2, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    except Exception as ex:
        logger.error("Exception during nodeos run: {0}".format(ex))
        eosio_tools.kill_process("./run_nodeos.pid", "nodeos", config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
        sys.exit(1)

def terminate_running_tasks():
    eosio_tools.kill_process("./run_nodeos.pid", "nodeos", config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    eosio_tools.kill_process("./run_keosd.pid", "keosd", config.KEOSD_IP_ADDRESS, config.KEOSD_PORT)
