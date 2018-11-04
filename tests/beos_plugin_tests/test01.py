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

args = None
logFile = None

nr_correct_tests = 0
nr_incorrect_tests = 0

def jsonArg(a):
    return " '" + json.dumps(a) + "' "

def run(args):
    print('test01.py:', args)
    logFile.write(args + '\n')
    if subprocess.call(args, shell=True):
      print('test01.py: exiting because of error')
      sys.exit(1)

def retry(args):
    while True:
        print('test01.py:', args)
        logFile.write(args + '\n')
        if subprocess.call(args, shell=True):
            print('*** Retry')
        else:
            break

def background(args, is_pipe = False ):
    print('test01.py:', args)
    logFile.write(args + '\n')
    if is_pipe:
      return subprocess.Popen( args, stdout=subprocess.PIPE, shell=True )
    else:
      return subprocess.Popen( args, shell=True )

def sleep(t):
    print('sleep', t, '...')
    time.sleep(t)
    print('resume')

def startWallet():
    run('rm -f ' + "~/eosio-wallet/default.wallet" )
    run('rm -rf ' + os.path.abspath(args.wallet_dir))
    run('mkdir -p ' + os.path.abspath(args.wallet_dir))
    sleep(.4)
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
        '    --enable-stale-production'
        '    --producer-name ' + account['name'] +
        '    --beos-config-file ' + args.beos_config +
        '    --signature-provider ' + account['pub'] + '=' + 'KEY:' + account['pvt'] + ' '
        '    --plugin eosio::http_plugin'
        '    --plugin eosio::chain_api_plugin'
        '    --plugin eosio::producer_plugin'
        '    --plugin eosio::beos_plugin'
        '    --plugin eosio::beos_api_plugin'
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
    sleep(1.5)

def stepStartWallet():
    startWallet()
    importKeys()

def stepStartBoot():
    startNode(0, {'name': 'eosio', 'pvt': args.private_key, 'pub': args.public_key})
    sleep(1.5)

def stepInstallSystemContracts():
    run(args.cleos + 'set contract eosio.token ' + args.contracts_dir + 'eosio.token/')

def stepCreateTokens():
    retry(args.cleos + 'push action eosio.token create \'["beos.token", "100000.0000 %s"]\' -p eosio.token' % (args.symbol))
    retry(args.cleos + 'push action eosio.token create \'["beos.token", "90000.0000 %s"]\' -p eosio.token' % (args.symbol_core))
    sleep(1)

def stepSetSystemContract():
    retry(args.cleos + 'set contract eosio ' + args.contracts_dir + 'eosio.system/')
    retry(args.cleos + 'set contract beos.init ' + args.contracts_dir + 'eosio.init/ -p beos.init')
    retry(args.cleos + 'set contract beos.token ' + args.contracts_dir + 'eosio.interchain/ -p beos.token')
    retry(args.cleos + 'set contract beos.market ' + args.contracts_dir + 'eosio.market/ -p beos.market')
    sleep(1)
    run(args.cleos + 'push action eosio setpriv' + jsonArg(['beos.market', 1]) + '-p eosio@active')
    run(args.cleos + 'push action eosio setpriv' + jsonArg(['beos.token', 1]) + '-p eosio@active')

def evaluate( pipe, true_mode = True ):
  try:

    global nr_correct_tests
    global nr_incorrect_tests

    out, err = pipe.communicate()

    #try:
    str = out.decode('UTF-8')
    json_out = json.loads( str )
    result = json_out['status']
    #except:
      #str = ""
      #result = "FAILED"

    info = "OK" if true_mode else "FAILED"

    if result == info:
      print('\nTest OK' )
      nr_correct_tests += 1
    else:
      print('\nTest FAILED' )
      nr_incorrect_tests += 1

    print('\nout: ', str )

  except Exception as e:
    print( "\nSomething went wrong during response evaluation: (", e, ")\n" )

def createAccount( creator, new_account, owner_key, active_key ):
  cpu = "0.0010 %s" % ( args.symbol )
  net = "0.0010 %s" % ( args.symbol )
  ram = "0.0010 %s" % ( args.symbol )

  command = " system newaccount %s %s %s %s --stake-cpu '%s' --stake-net '%s' --buy-ram '%s' " % ( creator, new_account, owner_key, active_key, cpu, net, ram )

  retry(args.cleos + command )

def createCommand( creator, account, owner_key, active_key, ram, account_contract, action, _from, quantity, create_account ):
  command = "{ \"creator\":\"%s\", \"account\":\"%s\", \"owner_key\":\"%s\", " % ( creator, account, owner_key )
  command += " \"active_key\": \"%s\", \"ram\":\"%s\", \"account_contract\":\"%s\", \"action\":\"%s\", " % ( active_key, ram, account_contract, action )
  command += " \"from\":\"%s\", \"quantity\":\"%s\", \"create_account\":%i }" % ( _from, quantity, create_account );
  return command

def correctTransfersButConfigFileIsWrong( server ):
  print("****************************CORRECT TRANSFERS ************************")

  creator = "eosio";
  account = "cfavocado1"
  owner_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
  active_key = "EOS6AAWx6uvqu5LMBt8vCNYXcxjrGmd3WvffxkBM4Uozs4e1dgBF3"
  ram = "0.0006 %s" % ( args.symbol )
  account_contract = "beos.token"
  action = "lock"
  _from = "beos.token"
  quantity = "200.0000 %s" % ( args.symbol )
  create_account = 1

  #creating account + locking
  command = createCommand( creator, account, owner_key, active_key, ram, account_contract, action, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )


def correctTransfers( server ):
  print("****************************CORRECT TRANSFERS ************************")

  creator = "eosio"
  account = "dude2"
  owner_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
  active_key = "EOS6AAWx6uvqu5LMBt8vCNYXcxjrGmd3WvffxkBM4Uozs4e1dgBF3"
  ram = "0.0006 %s" % ( args.symbol )
  account_contract = "beos.token"
  action = "lock"
  _from = "beos.token"
  quantity = "200.0000 %s" % ( args.symbol )
  create_account = 1

  #creating account + locking
  command = createCommand( creator, account, owner_key, active_key, ram, account_contract, action, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ) )

  #only locking. Account has to be created earlier
  account_ = "dude3"
  quantity_ = "100.0000 %s" % ( args.symbol )
  createAccount( creator, account_, owner_key, active_key )
  command = createCommand( creator, account, owner_key, active_key, ram, account_contract, action, _from, quantity_, 0 )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ) )

def incorrectTransfers( server ):
  print("****************************INCORRECT TRANSFERS ************************")

  creator = "eosio"
  account = "fbanana1"
  owner_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
  active_key = "EOS6AAWx6uvqu5LMBt8vCNYXcxjrGmd3WvffxkBM4Uozs4e1dgBF3"
  ram = "0.0006 %s" % ( args.symbol )
  account_contract = "beos.token"
  action = "lock"
  _from = "beos.token"
  quantity = "200.0000 %s" % ( args.symbol )
  create_account = 1

  #only locking. Account doesn't exist
  create_account_ = 0
  command = createCommand( creator, account, owner_key, active_key, ram, account_contract, action, _from, quantity, create_account_ )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

  #creating account + locking. Lack of permission for owner.
  account_ = "fbanana2"
  owner_key_ = "EOS5np7qxt1qkhffa9irgdpdSaEAC2LkDdbVtnj1GCgZT51sKhZgo"
  command = createCommand( creator, account_, owner_key_, active_key, ram, account_contract, action, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

  #creating account + locking. Incorrect owner key.
  account_ = "fbanana3"
  owner_key_ = "EOS5np7qxt1qkhffa9irgdpdXXXXC2LkDdbVtnj1GCgZT51sKhZgo"
  command = createCommand( creator, account_, owner_key_, active_key, ram, account_contract, action, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

  #creating account + locking. RAM = 0.
  account_ = "fbanana4"
  ram_ = "0.0000 %s" % ( args.symbol )
  command = createCommand( creator, account_, owner_key, active_key, ram_, account_contract, action, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

  #creating account + locking. Unknown creator
  account_ = "fbanana5"
  creator_ = "fake.eosio"
  command = createCommand( creator_, account_, owner_key, active_key, ram, account_contract, action, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

  #creating account + locking. Unknown action
  account_ = "fbananb1"
  action_ = "fake"
  command = createCommand( creator, account_, owner_key, active_key, ram, account_contract, action_, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

  #creating account + locking. Unknown contract
  account_ = "fbananb2"
  account_contract_ = "beos.fake"
  command = createCommand( creator, account_, owner_key, active_key, ram, account_contract_, action, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

  #creating account + locking. Unknown sender
  account_ = "fbananb3"
  _from_ = "fake"
  command = createCommand( creator, account_, owner_key, active_key, ram, account_contract, action, _from_, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

  #creating account + locking. A quantity equals to zero.
  account_ = "fbananb4"
  quantity = "0.0000 %s" % ( args.symbol )
  command = createCommand( creator, account_, owner_key, active_key, ram, account_contract, action, _from, quantity, create_account )
  evaluate( background( "curl --url " + server + " --data '" + command + "'", True ), False )

def transfers():
  try:

    server = "http://127.0.0.1:%s/v1/beos/transfer" % args.port

    index = args.beos_config_src.find( "fail" )

    if index == -1:
      correctTransfers( server )
      incorrectTransfers( server )
    else:
      correctTransfersButConfigFileIsWrong( server )

  except Exception as e:
    print( "\nSomething went wrong during transfers: (", e, ")\n" )

def summary():
  print("\n")
  print( "Number correct tests: %s\nNumber incorrect tests: %s" % ( nr_correct_tests, nr_incorrect_tests ) )
  print("\n")

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
parser.add_argument('--log-path', metavar='', help="Path to log file", default='./output.log')
parser.add_argument('--symbol', metavar='', help="The eosio.system symbol", default='PXBTS')
parser.add_argument('--symbol-core', metavar='', help="The eosio.system symbol-core", default='BEOS')
parser.add_argument('--port', metavar='', help="Port", default='8888')
parser.add_argument('--beos-config', metavar='', help="Config file for BEOS system", default='beos.config.ini')
parser.add_argument('--beos-config-src', metavar='', help="Config file for BEOS system", default='_beos.config.ini')

args = parser.parse_args()

logFile = open(args.log_path, 'a')
logFile.write('\n\n' + '*' * 80 + '\n\n\n')

args.cleos = args.main_dir + args.cleos
args.nodeos = args.main_dir + args.nodeos
args.keosd = args.main_dir + args.keosd
args.contracts_dir = args.main_dir + args.contracts_dir

with open('accounts.json') as f:
    a = json.load(f)
    firstProducer = len(a['users'])
    numProducers = len(a['producers'])
    accounts = a['users'] + a['producers'] + a['system_accounts']
    systemAccounts = a['system_accounts']

stepKillAll()
stepStartWallet()
stepStartBoot()
createSystemAccounts()
stepInstallSystemContracts()
stepCreateTokens()
stepSetSystemContract()
transfers()
stepKillAll()
summary()
