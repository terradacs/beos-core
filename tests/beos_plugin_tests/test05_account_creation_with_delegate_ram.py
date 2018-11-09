#!/usr/bin/env python3

import os
import sys
import json
import time
import random
import signal
import requests
import datetime
import argparse
import subprocess

args        = None

def run(args):
  print(' test05_account_creation_with_delegate_ram:', args)
  subprocess.call(args, shell=True)

def importKeys():
    run(args.cleos +'wallet import -n default-test05 --private-key ' + args.private_key)
    run(args.cleos +'wallet import -n default-test05 --private-key ' + args.gateway_private_key)

def startWallet():
    run('rm -f ' + "~/eosio-wallet/default-test05.wallet" )
    run('rm -rf ' + os.path.abspath(args.wallet_dir))
    run('mkdir -p ' + os.path.abspath(args.wallet_dir))
    time.sleep(.4)
    run(args.cleos + 'wallet create -n default-test05 --to-console' )

def stepStartWallet():
    startWallet()
    importKeys()

def askServer(_request, _isValid) :
    try:
        request=json.dumps(_request)
        server = "http://%s:%s/v1/beos/address_validator" % (args.ip_address, args.port)
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

def generate_name( val ):

  #".12345abcdefghijklmnopqrstuvwxyz"

  str_idx_name = str( val )

  result = ""
  for c in str_idx_name:
    result += chr( int(c) + 97 )

  return result

def createAccountsWithDelegateRAM():
  owner_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
  active_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
  ram = 5

  random.seed( time.time() )

  #searching 10 times not existing accounts
  for i in range( 0, 10 ):
    val_owner = random.randint( 10000, 10000000000 );

    #limit - only 12 chars
    val_new_account = random.randint( 100000000000, 999999999999 );

    #creating names according to EOS rules
    owner = generate_name( val_owner )
    new_account = generate_name( val_new_account )

    #checking if newly created names exist
    if validateAccount( owner, False ) and validateAccount( new_account, False ):
      break

  print("===== Creating accounts using delegateram action owner: %s new_account: %s =====" % ( owner, new_account ) )

  #creating 'owner' by 'beos.gateway'
  run(args.cleos +' --url http://%s:%s system newaccount beos.gateway %s %s %s --transfer-ram-kbytes %s' % (args.ip_address, args.port, owner, args.public_key, args.public_key, ram ) )
  ret_01 = validateAccount( owner, True )
  print("=====");

  #creating 'new_account' by 'owner' - false-test because 'owner' hasn't any resources
  run(args.cleos +' --url http://%s:%s system newaccount %s %s %s %s --transfer-ram-kbytes %s' % (args.ip_address, args.port, owner, new_account, owner_key, active_key, ram ) )
  ret_02 = validateAccount( new_account, False )
  print("=====");

  #adding resources to 'owner'
  run(args.cleos +'push action eosio initresource \'[ "%s", "1000000000", "100.0000 BEOS", "100.0000 BEOS" ]\' -p eosio' % ( owner ) )
  print("=====");

  #creating 'new_account' by 'owner'
  run(args.cleos +' --url http://%s:%s system newaccount %s %s %s %s --transfer-ram-kbytes %s' % (args.ip_address, args.port, owner, new_account, owner_key, active_key, ram ) )
  ret_03 = validateAccount( new_account, True )
  print("=====");

  if ret_01 and ret_02 and ret_03:
    print(datetime.datetime.now(),"[OK] This test has passed.")
    exit(0)
  else:
    print(datetime.datetime.now(),"[ERROR] This test has failed.")
    exit(1)

# Command Line Arguments
parser = argparse.ArgumentParser()


parser.add_argument('--gateway-private-key', metavar='', help="BEOS.GATEWAY Private Key", default='5Ka14byMGwBqE4Q149pffSjXf547otfZ1NKdTEq1ivwg9DjMoi6', dest="gateway_private_key")
parser.add_argument('--public-key', metavar='', help="EOSIO Public Key", default='EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV', dest="public_key")
parser.add_argument('--private-Key', metavar='', help="EOSIO Private Key", default='5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3', dest="private_key")
parser.add_argument('--ip-address', metavar='', help="Ip address of nodeos and keosd", default='127.0.0.1', dest="ip_address")
parser.add_argument('--port', metavar='', help="Port", default=8888)
parser.add_argument('--main-dir', metavar='', help="Main dictory for: cleos, nodeos, keosd", default='')
parser.add_argument('--cleos', metavar='', help="Cleos command", default='programs/cleos/cleos ')
parser.add_argument('--wallet-dir', metavar='', help="Path to wallet directory", default='./wallet/')

if __name__ == "__main__":
  args = parser.parse_args()
  args.cleos = args.main_dir + args.cleos

  try:
    stepStartWallet()
    createAccountsWithDelegateRAM()
  except Exception as _ex:
    print("[ERROR] Exeption `%s` occured while executing test05_account_creation_with_delegate_ram ."%(str(_ex)))

