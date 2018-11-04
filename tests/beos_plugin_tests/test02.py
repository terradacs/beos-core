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
from concurrent.futures import ThreadPoolExecutor

args = None
idx_name = 0

def jsonArg(a):
    return " '" + json.dumps(a) + "' "

def run(args):
    print('test02.py:', args)
    if subprocess.call(args, shell=True):
      print('test02.py: exiting because of error')
      sys.exit(1)

def retry(args):
    while True:
        print('test02.py:', args)
        if subprocess.call(args, shell=True):
            print('*** Retry')
        else:
            break

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
        '    --wasm-runtime wabt' +
        '    --producer-name ' + account['name'] +
        '    --beos-config-file ' + args.beos_config +
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

def createSystemAccounts():
    for a in systemAccounts:
      run(args.cleos + 'create account eosio ' + a["name"] + ' ' + args.public_key + ' ' + a["pub"] )

def stepKillAll():
    run('killall keosd nodeos || true')
    time.sleep( 1.5 )

def stepStartWallet():
    startWallet()
    importKeys()

def stepStartBoot():
    startNode(0, {'name': 'eosio', 'pvt': args.private_key, 'pub': args.public_key})
    time.sleep( 1.5 )

def stepInstallSystemContracts():
    run(args.cleos + 'set contract eosio.token ' + args.contracts_dir + 'eosio.token/')

def stepCreateTokens():
    retry(args.cleos + 'push action eosio.token create \'["beos.token", "100000.0000 %s"]\' -p eosio.token' % (args.symbol))
    retry(args.cleos + 'push action eosio.token create \'["beos.token", "90000.0000 %s"]\' -p eosio.token' % (args.symbol_core))
    time.sleep(1)

def stepSetSystemContract():
    retry(args.cleos + 'set contract eosio ' + args.contracts_dir + 'eosio.system/')
    retry(args.cleos + 'set contract beos.init ' + args.contracts_dir + 'eosio.init/ -p beos.init')
    retry(args.cleos + 'set contract beos.token ' + args.contracts_dir + 'eosio.interchain/ -p beos.token')
    retry(args.cleos + 'set contract beos.market ' + args.contracts_dir + 'eosio.market/ -p beos.market')
    time.sleep(1)
    run(args.cleos + 'push action eosio setpriv' + jsonArg(['beos.market', 1]) + '-p eosio@active')
    run(args.cleos + 'push action eosio setpriv' + jsonArg(['beos.token', 1]) + '-p eosio@active')

def createCommand( creator, account, owner_key, active_key, ram, account_contract, action, _from, quantity, create_account ):
  command = "{ \"creator\":\"%s\", \"account\":\"%s\", \"owner_key\":\"%s\", " % ( creator, account, owner_key )
  command += " \"active_key\": \"%s\", \"ram\":\"%s\", \"account_contract\":\"%s\", \"action\":\"%s\", " % ( active_key, ram, account_contract, action )
  command += " \"from\":\"%s\", \"quantity\":\"%s\", \"create_account\":%i }" % ( _from, quantity, create_account );
  return command

def generate_name():

  #".12345abcdefghijklmnopqrstuvwxyz"
  global idx_name

  str_idx_name = str( idx_name )
  idx_name += 1

  result = ""
  for c in str_idx_name:
    result += chr( int(c) + 97 )

  return result

def get_quantity( _quantity, prec = 4, bts_prec = 5 ):
  #[ 253586996, "a-342120073", "1.2.639561" ] ->  2535.8699

  quantity = str( _quantity )

  zeros = ''
  for i in range( len( quantity ), bts_prec + 1 ):
    zeros += '0'
  quantity = zeros + quantity

  res_div_mod = divmod( int( quantity ), pow( 10, bts_prec ) )

  if res_div_mod[0] == 0:
    return '', False

  str_base = str( res_div_mod[0] )

  start = len( str_base )
  end = len( quantity ) - 1

  str_prec = ""
  for i in range( start, end ):
    str_prec += quantity[i]

  return str_base + '.' + str_prec, True

def worker( params, server ):
  try:

    json_rpc_headers = {"content-type": "application/json"}
    ok = "OK"

    for i in range( args.nr_retries ):
      response = requests.post( server, data=params, headers=json_rpc_headers )
      response_json = response.json()
      print( response_json )

      if response_json['status'] == ok or ( not args.retry ):
        break
      time.sleep(.6)

  except Exception as e:
    print( "\nSomething went wrong during thread-response evaluation: (", e, ")\n" )

def _transfer( balances, server ):

  #Structure of balances tuple: [ 8, "a-0123", "1.2.821838" ]
  creator = "eosio"
  owner_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
  active_key = "EOS6AAWx6uvqu5LMBt8vCNYXcxjrGmd3WvffxkBM4Uozs4e1dgBF3"
  ram = "0.0006 %s" % ( args.symbol )
  account_contract = "beos.token"
  action = "lock"
  _from = "beos.token"
  create_account = 1

  done = False
  idx = 0
  buffer_length = 1000
  #futures = []

  while True:
    with ThreadPoolExecutor( max_workers = args.threads ) as executor:
      for i in range( args.threads ):

        if idx >= len( balances ):
          done = True
          break

        item = balances[ idx ]
        idx += 1

        account = generate_name()
        quantity, status = get_quantity( item[0] )

        if not status:
          continue

        quantity = quantity + " %s" % ( args.symbol )

        command = createCommand( creator, account, owner_key, active_key, ram, account_contract, action, _from, quantity, create_account )

        print( command + "\n" )
        future = executor.submit( worker, command, server )
      #   futures.append( future )

      # if ( idx % buffer_length ) == 0:
      #   for future in futures:
      #     if future.result() != None:
      #       print( future.result() )

      #   futures = []

    if done:
      break

def transfer():
  try:

    time.sleep(.4)

    server = "http://127.0.0.1:%s/v1/beos/transfer" % args.port

    balance_file = open( args.balances_file_path, 'r' )
    balances = json.load( balance_file )
    balances = balances[ "result" ]

    _transfer( balances, server )

  except Exception as e:
    print( "\nSomething went wrong during transfer: (", e, ")\n" )

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
createSystemAccounts()
stepInstallSystemContracts()
stepCreateTokens()
stepSetSystemContract()
transfer()
stepKillAll()
