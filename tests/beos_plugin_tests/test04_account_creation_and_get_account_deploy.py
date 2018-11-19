#!/usr/bin/env python3

import os
import json
import time
import string
import random
import signal
import requests
import datetime
import argparse

from testscenarios  import TestScenarios
from eosrpcexecutor import EOSRPCExecutor

args        = None


def random_user_name():
   return ''.join(random.choice(string.ascii_lowercase) for _ in range(12))

def createUserAccounts(_accouns_name):
    eosrpc = EOSRPCExecutor(args.nodeos_ip, args.nodeos_port, args.keosd_ip, args.keosd_port)
    cmd = [{
    "code":"eosio",
    "action":"newaccount",
    "authorized_by":"beos.gateway",
    "args":{
            "creator": "beos.gateway",
            "name": _accouns_name,
            "init_ram": 1,
            "owner": {
            "threshold": 1,
            "keys": [{
                "key": args.public_key,
                "weight": 1
                }
            ],
            "accounts": [],
            "waits": []
            },
            "active": {
            "threshold": 1,
            "keys": [{
                "key": args.public_key,
                "weight": 1
                }
            ],
            "accounts": [],
            "waits": []
            }
        }
    }]
    eosrpc.push_action(cmd)


def validateAccount(_name, _isValid):
    eosrpc = EOSRPCExecutor(args.nodeos_ip, args.nodeos_port, args.keosd_ip, args.keosd_port)
    account = eosrpc.get_account(_name)
    if _isValid:
        if "account_name" in account and account["account_name"] == _name:
            print(datetime.datetime.now(),"[OK] Validity for", _name,"address is as expected.")
            return True
        else:
            print(datetime.datetime.now(),"[ERROR] Inconsistent 'is_valid' state for account", _name,".")
            return False
    else :
        if "account_name" in account and account["account_name"] == _name:
            print(datetime.datetime.now(),"[ERROR] Inconsistent 'is_valid' state for account",_name,".")
            return False
        else:
            print(datetime.datetime.now(),"[OK] Validity for", _name,"address is as expected.")
            return True

    
def printSummary(_test_passed):
    if _test_passed:
        print(datetime.datetime.now(),"[OK] This test has pass.")
        exit(0)
    else:
        print(datetime.datetime.now(),"[ERROR] This test has failed.")
        exit(1)

def kill_nodeos_and_keosd():
  os.system("pkill keosd")
  os.system("pkill nodeos")

# Command Line Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--nodeos-ip', metavar='', help="Ip address of nodeos ", default='127.0.0.1', dest="nodeos_ip")
parser.add_argument('--keosd-ip', metavar='', help="Ip address of keosd", default='127.0.0.1', dest="keosd_ip")
parser.add_argument('--public-key', metavar='', help="EOSIO Public Key", default='EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV', dest="public_key")
parser.add_argument('--private-Key', metavar='', help="EOSIO Private Key", default='5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3', dest="private_key")
parser.add_argument('--nodeos-port', metavar='', help="Port", default='8888')
parser.add_argument('--keosd-port', metavar='', help="Port", default='8900')
parser.add_argument('--deploy-script-pwd', metavar='', help="Path to deploy.py" )

if __name__ == "__main__":
  test_passed = False
  args = parser.parse_args()

  try:
      time.sleep(2)
      created_user = random_user_name()
      createUserAccounts(created_user)
      time.sleep(2)
      random_name = random_user_name()
      dude1validity = validateAccount(created_user, True)
      dude2validity = validateAccount(random_name, False)
      if dude1validity and dude2validity :
          test_passed = True
  except Exception as _ex:
    print("[ERROR] Exeption `%s` occured while executing test04_account_creation_and_get_account ."%(str(_ex)))
  finally:
    printSummary(test_passed)


