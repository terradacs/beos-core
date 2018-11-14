#!/usr/bin/env python3

import os
import json
import time
import string
import random
import requests
import datetime
import argparse

from testscenarios  import TestScenarios
from eosrpcexecutor import EOSRPCExecutor

args        = None

def random_user_name():
   return ''.join(random.choice(string.ascii_lowercase) for _ in range(12))

def createUserAccounts(_account_name):
    eosrpc = EOSRPCExecutor(args.nodeos_ip, args.nodeos_port, args.keosd_ip, args.keosd_port)
    cmd = [{
    "code":"eosio",
    "action":"newaccount",
    "authorized_by":"beos.gateway",
    "args":{
            "creator": "beos.gateway",
            "name": _account_name,
            "init_ram" : 1,
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


def askServer(_request, _isValid) :
    try:
        request=json.dumps(_request)
        server = "http://%s:%s/v1/beos/address_validator" % (args.nodeos_ip, args.nodeos_port)
        json_rpc_headers = {"content-type": "application/json"}
        response = requests.post( server, data=request, headers=json_rpc_headers )
        response_json = response.json()
        print(datetime.datetime.now(),"Server response" ,response_json )
        if response_json['is_valid'] != _isValid:
            print(datetime.datetime.now(),"[ERROR] Inconsistent 'is_valid' state for account", _request["account_name"],".")
            return False
        else :
            print(datetime.datetime.now(),"[OK] Validity for", _request["account_name"],"address is as expected.")
            return True
    except Exception as _ex:
        print(datetime.datetime.now(),"[ERROR] Something goes wrong during address validation: ", _ex)
        return False


def validateAccount(_name, _isValid):
    command = {"account_name":_name}
    return askServer(command, _isValid)

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
    print("[ERROR] Exeption `%s` occured while executing test05_account_creation_and_account_validator ."%(str(_ex)))
  finally:
    printSummary(test_passed)

