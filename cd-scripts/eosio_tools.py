#!/usr/bin/python3

import subprocess
import logging
import os
import time
import sys
import json
import datetime
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
except Exception as ex:
    msg = "config.py is not present. Please make a copy of config-example.py and name it as config.py. Edit config.py to customize your build environment."
    print(msg)

MODULE_NAME = "EOSIO Tools Py"
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

def get_last_get_info(nodeos_ip, nodeos_port, timeout = 60., use_https = False):
    import requests
    prefix = "http://"
    if use_https:
        prefix = "https://"
    step = 0.25
    timeout_cnt = 0.
    url = prefix + "{0}:{1}/v1/chain/get_info".format(nodeos_ip, nodeos_port)
    while True:
        try:
            response = requests.get(url)
            if  response.status_code == 200:
                return response.json()
        except:
            pass
        time.sleep(step)
        timeout_cnt += step
        if timeout_cnt >= timeout:
            raiseEOSIOException("Timeout during get_last_block_number_rpc")

def get_last_block_number(nodeos_ip, nodeos_port, timeout = 60., use_https = False):
    return get_last_get_info(nodeos_ip, nodeos_port, timeout, use_https)['head_block_num']
   
def get_last_irreversible_block_number(nodeos_ip, nodeos_port, timeout = 60., use_https = False):
    return get_last_get_info(nodeos_ip, nodeos_port, timeout, use_https)['last_irreversible_block_num']

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