#!/usr/bin/env python3

import argparse
import json
import numpy
import os
import random
import re
import subprocess
import sys
import time
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor

args = None
idx_name = 0
test_failed = False

def jsonArg(a):
    return " '" + json.dumps(a) + "' "

def run(args):
    print(' test02.py:', args)
    if subprocess.call(args, shell=True):
      print(datetime.datetime.now,'test02.py: exiting because of error')
      sys.exit(1)

def background(args, is_pipe = False ):
    print('test02.py:', args)
    if is_pipe:
      return subprocess.Popen( args, stdout=subprocess.PIPE, shell=True )
    else:
      return subprocess.Popen( args, shell=True )

def startWallet():
    run('rm -f ' + "~/eosio-wallet/default.wallet" )
    run('rm -rf ' + os.path.abspath(args.wallet_dir))
    run('mkdir -p ' + os.path.abspath(args.wallet_dir))
    time.sleep(.4)
    run(args.cleos + 'wallet create --to-console' )

def importKeys():
    run(args.cleos + 'wallet import --private-key ' + args.private_key)
    keys = {}
    for a in accounts:
        key = a['pvt']
        if not key in keys:
            keys[key] = True
            run(args.cleos + 'wallet import --private-key ' + key)

def startNode(nodeIndex, account):
    print("****************************START NODE ************************")
    dir = args.nodes_dir + ('%02d-' % nodeIndex) + account['name'] + '/'
    run('rm -rf ' + dir)
    run('mkdir -p ' + dir)
    run('rm -f ' + args.beos_config )
    run('cp ' + args.beos_config_src + ' ' + args.beos_config )

    cmd = (
        args.nodeos +
        '    --max-irreversible-block-age -1'
        '    --contracts-console'
        '    --genesis-json ' + os.path.abspath(args.genesis) +
        '    --blocks-dir ' + os.path.abspath(dir) + '/blocks'
        '    --config-dir ' + os.path.abspath(dir) +
        '    --data-dir ' + os.path.abspath(dir) +
        '    --chain-state-db-size-mb 1024'
        '    --http-server-address 127.0.0.1:%s' % args.port +
        '    --enable-stale-production' +
        '    --wasm-runtime binaryen' +
        '    --producer-name ' + account['name'] +
        '    --signature-provider ' + account['pub'] + '=' + 'KEY:' + account['pvt'] + ' '
        '    --plugin eosio::http_plugin'
        '    --plugin eosio::chain_api_plugin'
        '    --plugin eosio::producer_plugin'
        '    --plugin eosio::beos_plugin'
        '    --plugin eosio::beos_api_plugin'
        '    --plugin eosio::history_plugin'
        '    --plugin eosio::history_api_plugin '
          )
    with open(dir + 'stderr', mode='w') as f:
        f.write(cmd + '\n\n')

    #background( cmd + '    2>>' + dir + 'stderr' )
    background( cmd )

def stepKillAll():
    run('killall keosd nodeos || true')
    time.sleep( 1.5 )

def stepStartWallet():
    startWallet()
    importKeys()

def stepStartBoot():
    startNode(0, {'name': 'eosio', 'pvt': args.private_key, 'pub': args.public_key})
    time.sleep( 1.5 )

def askServer(_request, _isValid) :
    try:
        request=json.dumps(_request)
        server = "http://127.0.0.1:%s/v1/beos/address_validator" % args.port
        json_rpc_headers = {"content-type": "application/json"}
        response = requests.post( server, data=request, headers=json_rpc_headers )
        response_json = response.json()
        print(datetime.datetime.now(),"Server response" ,response_json )
        if response_json['is_valid'] != _isValid:
            global test_failed
            print(datetime.datetime.now(),"[ERROR] Inconsistent 'is_valid' state for account", _request["account_name"],".")
            test_failed=True
        else :
            print(datetime.datetime.now(),"[OK] Validity for", _request["account_name"],"address is as expected.")
    except Exception as _ex:
        print(datetime.datetime.now(),"[ERROR] Something goes wrong during address validation: ", _ex)

def validateAccount(_name, _isValid):
    command = {"account_name":_name}
    askServer(command, _isValid)


def printSummary():
    global test_failed
    if test_failed:
        print(datetime.datetime.now(),"[ERROR] This test has failed.")
    else:
        print(datetime.datetime.now(),"[OK] This test has pass.")

# Command Line Arguments
parser = argparse.ArgumentParser()

parser.add_argument('--public-key', metavar='', help="EOSIO Public Key", default='EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV', dest="public_key")
parser.add_argument('--private-Key', metavar='', help="EOSIO Private Key", default='5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3', dest="private_key")
parser.add_argument('--main-dir', metavar='', help="Main dictory for: cleos, nodeos, keosd", default='')
parser.add_argument('--cleos', metavar='', help="Cleos command", default='programs/cleos/cleos ')
parser.add_argument('--nodeos', metavar='', help="Path to nodeos binary", default='programs/nodeos/nodeos ')
parser.add_argument('--keosd', metavar='', help="Path to keosd binary", default='programs/keosd/keosd ')
parser.add_argument('--contracts-dir', metavar='', help="Path to contracts directory", default='contracts/')
parser.add_argument('--nodes-dir', metavar='', help="Path to nodes directory", default='./nodes/')
parser.add_argument('--genesis', metavar='', help="Path to genesis.json", default="./genesis.json")
parser.add_argument('--wallet-dir', metavar='', help="Path to wallet directory", default='./wallet/')
parser.add_argument('--symbol', metavar='', help="The eosio.system symbol", default='PXBTS')
parser.add_argument('--port', metavar='', help="Port", default='8888')
parser.add_argument('--beos-config', metavar='', help="Config file for BEOS system", default='beos.config.ini')
parser.add_argument('--beos-config-src', metavar='', help="Config file for BEOS system", default='_beos.config.ini')
parser.add_argument('--balances-file-path', metavar='', help="File with all balances from bitshares blockchain", default='./bts_balances.json')
parser.add_argument('--threads', metavar='', help="Number of threads", type=int, default=30 )
parser.add_argument('--retry', metavar='', help="Allow to retry newaccount transaction", type=int, default=1 )
parser.add_argument('--nr-retries', metavar='', help="Number of retries", type=int, default=5 )

args = parser.parse_args()

args.cleos = args.main_dir + args.cleos
args.nodeos = args.main_dir + args.nodeos
args.keosd = args.main_dir + args.keosd
args.contracts_dir = args.main_dir + args.contracts_dir
with open('accounts.json') as f:
    a = json.load(f)
    accounts = a['users'] + a['producers'] + a['system_accounts']
    systemAccounts = a['system_accounts']

stepKillAll()
stepStartWallet()
stepStartBoot()
validateAccount("eosio",True)
validateAccount("ugabuga", False)
stepKillAll()
printSummary()
