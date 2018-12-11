#!/usr/bin/python3

import subprocess
import logging
import os
import time
import sys
import json
import datetime

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

fh = logging.FileHandler(config.MAIN_LOG_PATH)
fh.setLevel(config.LOG_LEVEL)
fh.setFormatter(logging.Formatter(config.LOG_FORMAT))

logger.addHandler(ch)
logger.addHandler(fh)

class EOSIOException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

def raiseEOSIOException(msg):
    logger.error(msg)
    raise EOSIOException(msg)

def save_screen_cfg(cfg_file_name, log_file_path):
    with open(cfg_file_name, "w") as cfg:
        cfg.write("logfile {0}\n".format(log_file_path))
        cfg.write("deflog on\n")
        cfg.write("logfile flush 1\n")

def save_pid_file(pid_file_name, exec_name):
    with open(pid_file_name, "w") as pid_file:
            pid_file.write("{0}-{1}\n".format(exec_name, datetime.datetime.now().strftime("%Y-%m-%d")))

def wait_for_string_in_file(log_file_name, string, timeout):
    step = 0.5
    to_timeout = 0.
    while True:
        time.sleep(step)
        to_timeout = to_timeout + step
        if to_timeout > timeout:
            msg = "Timeout during wait for string {0}".format(string)
            print(msg)
            raise EOSIOException(msg)
        if not os.path.exists(log_file_name):
            continue
        with open(log_file_name, "r") as log_file:
            leave = False
            for line in log_file.readlines():
                if string in line:
                    leave = True
                    break
            if leave:
                break

def get_last_line_of_file(file_name):
    last_line = ""
    with open(file_name, "r") as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR) 
        last_line = f.readline().decode()
    return last_line

def get_last_block_number_from_log_file(nodeos_log_file_name, timeout = 60.):
    import re
    last_block_number = -1
    step = 0.5
    timeout_cnt = 0.
    while True:
        line = get_last_line_of_file(nodeos_log_file_name)
        if "] Produced block" in line:
            ret = re.search('\#[0-9] @', line)
            ret = ret.group(0)
            last_block_number = int(ret[1:-1])
            break
        time.sleep(step)
        timeout_cnt += step
        if timeout_cnt >= timeout:
            raiseEOSIOException("Timeout during get_last_block_number_from_log_file")
    return last_block_number

def wait_for_blocks_produced_from_log_file(block_count, nodeos_log_file_name, timeout = 60.):
    logger.info("Waiting for {0} blocks to be produces...".format(block_count))
    last_block_number = get_last_block_number_from_log_file(nodeos_log_file_name, timeout)
    while True:
        curr_block_number = get_last_block_number_from_log_file(nodeos_log_file_name, timeout)
        if curr_block_number - last_block_number > block_count:
            return

def get_last_block_number(nodeos_ip, nodeos_port, timeout = 60., use_https = False):
    import requests
    prefix = "http://"
    if use_https:
        prefix = "https://"
    step = 0.5
    timeout_cnt = 0.
    url = prefix + "{0}:{1}/v1/chain/get_info".format(nodeos_ip, nodeos_port)
    while True:
        try:
            response = requests.get(url)
            if  response.status_code == 200:
                response_json = response.json()
                return int(response_json['head_block_num'])
        except:
            pass
        time.sleep(step)
        timeout_cnt += step
        if timeout_cnt >= timeout:
            raiseEOSIOException("Timeout during get_last_block_number_rpc")

def wait_for_blocks_produced(block_count, nodeos_ip, nodeos_port, timeout = 60., use_https = False):
    logger.info("Waiting for {0} blocks to be produced...".format(block_count))
    last_block_number = get_last_block_number(nodeos_ip, nodeos_port, timeout, use_https)
    while True:
        curr_block_number = get_last_block_number(nodeos_ip, nodeos_port, timeout, use_https)
        if curr_block_number - last_block_number > block_count:
            return

def kill_process(pid_file_name, proc_name, ip_address, port):
    pids = []
    pid_name = None
    try:
        with open(pid_file_name, "r") as pid_file:
            pid_name = pid_file.readline()
            pid_name = pid_name.strip()
        if pid_name is not None:
            for line in os.popen("ps ax | grep " + proc_name + " | grep -v grep"):
                if pid_name in line:
                    line = line.strip().split()
                    pids.append(line[0])
            for pid in pids:
                for line in os.popen("ps --no-header --ppid {0}".format(pid)):
                    line = line.strip().split()
                    os.kill(int(line[0]), 2)
                os.kill(int(pid), 2)
            if os.path.exists(pid_file_name):
                os.remove(pid_file_name)
    except Exception as ex:
        logger.warning("Process {0} cannot be killed. Reason: {1}".format(proc_name, ex))

def run_command(parameters):
    ret = subprocess.run(parameters, stdout=config.log_main, stderr=config.log_main)
    retcode = ret.returncode
    if retcode == 0:
        logger.debug("Executed with ret: {0}".format(ret))
    else:
        logger.error("Executed with ret: {0}".format(ret))
        raiseEOSIOException("Initialization failed on last command")

def run_command_and_return_output(parameters):
    ret = subprocess.run(parameters, stdout=subprocess.PIPE)
    retcode = ret.returncode
    if retcode == 0:
        logger.debug("Executed with ret: {0}".format(ret))
    else:
        logger.error("Executed with ret: {0}".format(ret))
        raiseEOSIOException("Initialization failed on last command")
    return ret.stdout

def show_wallet_unlock_postconf():
    wallet_password = None
    with open(config.WALLET_PASSWORD_PATH, "r") as password_file:
        wallet_password = password_file.readline()
        #wallet_password = wallet_password[1:-1] # remove " character from begin and end of string

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

    parameters = [
        config.NODEOS_EXECUTABLE,
        "--contracts-console",
        "--blocks-dir", os.path.abspath(working_dir) + '/blocks',
        "--config-dir", os.path.abspath(working_dir),
        "--data-dir", os.path.abspath(working_dir),
    ]

    logger.info("Configuration complete, you can now run nodeos with command (consider running in screen): {0}".format(" ".join(parameters)))

def detect_process_by_name(proc_name, ip_address, port):
    pids = []
    for line in os.popen("ps ax | grep " + proc_name + " | grep -v grep"):
        if ip_address in line and str(port) in line:
            line = line.strip().split()
            pids.append(line[0])
    if pids:
        raiseEOSIOException("{0} process is running on {1}:{2}. Please terminate that process and try again.".format(proc_name, ip_address, port))

def get_log_file_name(executable, date = datetime.datetime.now().strftime("%Y-%m-%d")):
    return "./{0}-{1}.log".format(executable, date)

def get_screen_name(executable, date = datetime.datetime.now().strftime("%Y-%m-%d")):
    return "{0}-{1}".format(executable, date)

def run_keosd(ip_address, port, wallet_dir, use_https = False, forceWalletCleanup = False):
    from sys import exit
    logger.info("*** Running KLEOSD at {0}:{1} in {2}".format(ip_address, port, wallet_dir))
    detect_process_by_name("keosd", ip_address, port)
    
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

    log_file_name = get_log_file_name("keosd")
    if os.path.exists(log_file_name):
        move(log_file_name, log_file_name + ".old")

    parameters = None
    if use_https:
        # run kleosd in https mode
        parameters = [
            config.KEOSD_EXECUTABLE,
            "--https-server-address","{0}:{1}".format(ip_address, port),
            "--https-certificate-chain-file", config.KEOSD_CERTIFICATE_CHAIN_FILE,
            "--https-private-key-file", config.KEOSD_PRIVATE_KEY_FILE,
            "--wallet-dir", wallet_dir,
        ]
    else:
        # run kleosd in http mode
        parameters = [
            config.KEOSD_EXECUTABLE,
            "--http-server-address","{0}:{1}".format(ip_address, port) ,
            "--wallet-dir", wallet_dir,
        ]
    
    save_screen_cfg("./keosd_screen.cfg", log_file_name)
    screen_params = [
        "screen",
        "-m",
        "-d",
        "-L",
        "-c",
        "./keosd_screen.cfg",
        "-S",
        get_screen_name("keosd")
    ]

    parameters = screen_params + parameters
    logger.info("Running keosd with command: {0}".format(" ".join(parameters)))
    try:
        subprocess.Popen(parameters)
        save_pid_file("./run_keosd.pid", "keosd")
        wait_for_string_in_file(log_file_name, "add api url: /v1/wallet/unlock", 10.)
    except Exception as ex:
        logger.error("Exception during keosd run: {0}".format(ex))
        kill_process("./run_keosd.pid", "keosd", ip_address, port)
        sys.exit(1)

def unlock_wallet(wallet_name, wallet_password):
    parameters = [config.CLEOS_EXECUTABLE, 
        "wallet", "unlock", 
        "-n", wallet_name, 
        "--password", wallet_password
    ]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    run_command(parameters)

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
        run_command(parameters)
    else:
        raiseEOSIOException("Importing empty key!")

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
    run_command(parameters)

    if unlock:
        wallet_password = None
        with open(config.WALLET_PASSWORD_PATH, "r") as password_file:
            wallet_password = password_file.readline()
            #wallet_password = wallet_password[1:-1] # remove " character from begin and end of string
        unlock_wallet(config.MASTER_WALLET_NAME, wallet_password)

    for key in config.SYSTEM_ACCOUNT_KEYS:
        import_key(config.MASTER_WALLET_NAME, key, wallet_url)

def run_nodeos(node_index, name, public_key, use_https = False):
    detect_process_by_name("nodeos", config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    if not public_key:
        logger.error("Public key is empty, aborting")
        raise EOSIOException("Public key is empty, aborting")
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
        raiseEOSIOException("File {0} does not exists.".format(config.GENESIS_JSON_FILE_SRC))
        
    logger.info("Copying config file from {0} to {1}".format(config.BEOS_CONFIG_FILE_SRC, working_dir + config.BEOS_CONFIG_FILE))
    if os.path.exists(config.BEOS_CONFIG_FILE_SRC):
        copy(config.BEOS_CONFIG_FILE_SRC, working_dir + config.BEOS_CONFIG_FILE)
    else:
        raiseEOSIOException("File {0} does not exists.".format(config.BEOS_CONFIG_FILE_SRC))

    log_file_name = get_log_file_name("nodeos")
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

    save_screen_cfg("./nodeos_screen.cfg", log_file_name)
    screen_params = [
        "screen",
        "-m",
        "-d",
        "-L",
        "-c",
        "./nodeos_screen.cfg",
        "-S",
        "{0}-{1}".format("nodeos", datetime.datetime.now().strftime("%Y-%m-%d"))
    ]

    parameters = screen_params + parameters
    logger.info("Running nodeos with command: {0}".format(" ".join(parameters)))
    try:
        subprocess.Popen(parameters)
        save_pid_file("./run_nodeos.pid", "nodeos")
        wait_for_blocks_produced(2, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    except Exception as ex:
        logger.error("Exception during nodeos run: {0}".format(ex))
        kill_process("./run_nodeos.pid", "nodeos", config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
        sys.exit(1)

def create_account(creator, name, owner_key, active_key, transfer_ram = False, schema = "http"):
    if not owner_key and not active_key:
        logger.error("Owner key or active key are empty, aborting")
        raise EOSIOException("Owner key or active key are empty, aborting")
    parameters = [config.CLEOS_EXECUTABLE, 
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "create", "account"]
    if transfer_ram:
        parameters.append("--transfer-ram")
    parameters += [creator, name, owner_key, active_key]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    run_command(parameters)

def set_contract(account, contract, permission, schema = "http"):
    parameters = [config.CLEOS_EXECUTABLE, 
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "set", "contract", account, contract, "-p", permission]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    run_command(parameters)
    time.sleep(2)

def push_action(account, action, data, permission, schema = "http"):
    parameters = [config.CLEOS_EXECUTABLE, 
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "push", "action", account, action, data, "-p", permission]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    run_command(parameters)
    time.sleep(2)

def get_balance(_account_name, _currency, schema = "http"):
    parameters = [config.CLEOS_EXECUTABLE, 
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "get", "currency", "balance", "eosio.token", _account_name, _currency]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    return float(run_command_and_return_output(parameters).decode('utf-8').split()[0])

def get_account(_account_name, schema = "http"):
    time.sleep(2)
    parameters = [config.CLEOS_EXECUTABLE, 
        "--url", "{0}://{1}:{2}".format(schema, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "--wallet-url", "{0}://{1}:{2}".format(schema, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "get", "account", "-j", _account_name]
    logger.info("Executing command: {0}".format(" ".join(parameters)))
    #logger.info(json.dumps(json.loads(run_command_and_return_output(parameters)),indent=2,separators=(',', ': ')))
    logger.info(run_command_and_return_output(parameters))

def terminate_running_tasks(nodeos, keosd):
    from signal import SIGINT
    #Just to produce few blocks and accept lately scheduled transaction(s)
    time.sleep(4)

    if nodeos is not None:
        logger.info("Terminating NODEOS")
        nodeos.send_signal(SIGINT)
        nodeos.wait()

