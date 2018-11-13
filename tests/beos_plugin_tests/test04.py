#!/usr/bin/env python3

import os
import re
import sys
import json
import numpy
import time
import random
import signal
import requests
import datetime
import argparse
import subprocess

from testscenarios import TestScenarios

args = None
nodeos_proc = None


def jsonArg(a):
    return " '" + json.dumps(a) + "' "


def run(args):
    print(' test04.py:', args)
    if subprocess.call(args, shell=True):
      print(datetime.datetime.now,'test04.py: exiting because of error')
      sys.exit(1)


def retry(args):
    while True:
        print('test04.py:', args)
        if subprocess.call(args, shell=True):
            print('*** Retry')
        else:
            break


def background(args, is_pipe = False ):
    print('test04.py:', args)
    if is_pipe:
      return subprocess.Popen( args, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid )
    else:
      return subprocess.Popen( args, shell=True, preexec_fn=os.setsid )


def importKeys():
    run(args.cleos + getNodesAndKeosd() +'wallet import -n default-test04 --private-key ' + args.private_key)
    keys = {}
    for a in accounts:
        key = a['pvt']
        if not key in keys:
            keys[key] = True
            run(args.cleos +' --no-auto-keosd '+ getNodesAndKeosd() +'wallet import -n default-test04 --private-key ' + key)


def startNode(nodeIndex, account):
    print("****************************START NODE ************************")
    dir = args.nodes_dir + ('%02d-' % nodeIndex) + account['name'] + '/'
    run('rm -rf ' + dir)
    run('mkdir -p ' + dir)
    run('rm -f ' + args.beos_config )
    run('cp ' + args.beos_config_src + ' ' + args.beos_config )
    run('[ -f "_config_example.ini" ] && cp _config_example.ini ' + dir +'/config.ini ')

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
        '    --plugin eosio::wallet_api_plugin '
        '    --plugin eosio::wallet_plugin '
          )
    with open(dir + 'stderr', mode='w') as f:
        f.write(cmd + '\n\n')

    global nodeos_proc
    nodeos_proc = background( cmd )

def createSystemAccounts():
    for a in systemAccounts:
      print("Creating system account: ", a["name"])
      run(args.cleos+ getNodesAndKeosd() +' create account eosio ' + a["name"] + ' ' + args.public_key + ' ' + a["pub"] )

def createUserAccounts():
    for a in userAccounts:
      print("Creating user account: ", a["name"])
      retry(args.cleos+ getNodesAndKeosd() +' push action beos.token newaccount \'['
      + "eosio" + ","
      + a["name"] + ","
      + args.public_key + ","
      + args.public_key + ","
      + str(30000) + "," + str(0) + "," + str(0) + "]\' -p eosio@active" )


def startWallet():
    run('rm -f ' + "~/eosio-wallet/default-test04.wallet" )
    run('rm -rf ' + os.path.abspath(args.wallet_dir))
    run('mkdir -p ' + os.path.abspath(args.wallet_dir))
    time.sleep(.4)
    run(args.cleos + getNodesAndKeosd() + 'wallet create -n default-test04 --to-console' )


def stepKillStartedNode():
    global nodeos_proc
    if nodeos_proc:
      print("Killing nodeos with pid", nodeos_proc.pid)
      os.killpg(os.getpgid(nodeos_proc.pid), signal.SIGTERM)
    time.sleep( 1.5 )

def stepStartWallet():
    startWallet()
    importKeys()

def stepStartBoot():
    startNode(0, {'name': 'eosio', 'pvt': args.private_key, 'pub': args.public_key})
    time.sleep( 1.5 )

def getNodesAndKeosd():
  return ' -u http://127.0.0.1:' + args.port+ ' --wallet-url=http://127.0.0.1:8900 ' 

def stepInstallSystemContracts():
    run(args.cleos  + getNodesAndKeosd() +' set contract eosio.token ' + args.contracts_dir + 'eosio.token/')

def stepCreateTokens():
    retry(args.cleos + getNodesAndKeosd() +' push action eosio.token create \'["beos.token", "100000.0000 %s"]\' -p eosio.token'%(args.symbol))
    retry(args.cleos + getNodesAndKeosd() +' push action eosio.token create \'["beos.token", "90000.0000 %s"]\' -p eosio.token'%(args.symbol_core))
    time.sleep(1)

def stepSetSystemContract():
    retry(args.cleos +getNodesAndKeosd() +' set contract eosio ' + args.contracts_dir + 'eosio.system/')
    retry(args.cleos +getNodesAndKeosd() +' set contract beos.init ' + args.contracts_dir + 'eosio.init/ -p beos.init')
    retry(args.cleos +getNodesAndKeosd() +' set contract beos.token ' + args.contracts_dir + 'eosio.interchain/ -p beos.token')
    retry(args.cleos +getNodesAndKeosd() +' set contract beos.market ' + args.contracts_dir + 'eosio.market/ -p beos.market')
    time.sleep(1)
    run(args.cleos +getNodesAndKeosd() +' push action eosio setpriv' + jsonArg(['beos.market', 1]) + '-p eosio@active')
    run(args.cleos +getNodesAndKeosd() +' push action eosio setpriv' + jsonArg(['beos.token', 1]) + '-p eosio@active')

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
parser.add_argument('--symbol-core', metavar='', help="The eosio.system symbol-core", default='BEOS')
parser.add_argument('--port', metavar='', help="Port", default='8999')
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
    userAccounts = a['users']

if __name__ == "__main__":
  scenarios = TestScenarios('http://127.0.0.1', args.port, 'http://127.0.0.1', '8900')
  try:
    for scenario in scenarios:
      stepKillStartedNode()
      stepStartWallet()
      stepStartBoot()
      createSystemAccounts()
      stepInstallSystemContracts()
      stepCreateTokens()
      stepSetSystemContract()
      createUserAccounts()
      time.sleep(1)
      scenario.make_scenario_actions()
      scenario.wait_for_end()
      scenario.get_scenario_summary()
  except Exception as _ex:
    print("[ERROR] Exeption `%s` occured while executing scenario `%s`."%(str(_ex), scenario.get_current_scenario()))
  finally:
    scenarios.stop_scenarios()
    stepKillStartedNode()

