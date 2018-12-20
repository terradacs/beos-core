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

accounts_names = []
producers_names = []
owner_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
active_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"

def run(args):
  #print(' test07:', args)
  subprocess.call(args, shell=True)

def importKeys():
    run(args.cleos +'wallet import -n default-test07 --private-key ' + args.private_key)
    run(args.cleos +'wallet import -n default-test07 --private-key ' + args.gateway_private_key)

def startWallet():
    run('rm -f ' + "~/eosio-wallet/default-test07.wallet" )
    run('rm -rf ' + os.path.abspath(args.wallet_dir))
    run('mkdir -p ' + os.path.abspath(args.wallet_dir))
    time.sleep(.4)
    run(args.cleos + 'wallet create -n default-test07 --to-console' )

def stepStartWallet():
    startWallet()
    importKeys()

def askServer(_data, _endpoint) :
    try:
        request=json.dumps(_data)
        server = "http://%s:%s/v1/%s" % (args.nodeos_ip, args.nodeos_port, _endpoint)
        json_rpc_headers = {"content-type": "application/json"}
        response = requests.post( server, data=request, headers=json_rpc_headers )
        response_json = response.json()
        return response_json
    except Exception as _ex:
        print(datetime.datetime.now(),"[ERROR] Something goes wrong during address validation: ", _ex)
        return False

def getBlock() :
    try:
        request = ""
        server = "http://%s:%s/v1/chain/get_info" % (args.nodeos_ip, args.nodeos_port)
        json_rpc_headers = {"content-type": "application/json"}
        response = requests.post( server, data=request, headers=json_rpc_headers )
        response_json = response.json()

        return response_json["head_block_num"]

    except Exception as _ex:
        print( _ex )
        return 0

# Validation and check functions

def validateAccount(_name, _isValid):
  data = {"account_name":_name}
  res = askServer(data, 'beos/address_validator')
  if res['is_valid'] != _isValid:
    return False
  else :
    return True

def validateIssue(_name, _isValid):
  data = {"account": _name, "code": "eosio.token", "symbol": "PXBTS"}
  res = askServer(data, 'chain/get_currency_balance')
  if res[0] != '1.0000 PXBTS':
    return False
  else:
    return True

def validateProducersQuantity():
  data = {"limit": 50, "lower_bound": "", "json": True }
  res = askServer(data, 'chain/get_producers')
  if len(res['rows']) != (len(producers_names) + 1):
    return False
  else:
    return True

def getAccountData(account_name):
  data = {"account_name": account_name}
  res = askServer(data, 'chain/get_account')
  return res

def isProducerRegistered(producer_name):
  data = {"limit": 50, "lower_bound": "", "json": True }
  res = askServer(data, 'chain/get_producers')
  for row in res['rows']:
    if row['owner'] == producer_name:
      if row['producer_key'] == 'EOS1111111111111111111111111111111114T1Anm':
        return False
      return True
  return False

def checkVotesForProducer(producer_name):
  data = {"limit": 50, "lower_bound": "", "json": True }
  res = askServer(data, 'chain/get_producers')
  for row in res['rows']:
    if row['owner'] == producer_name:
      return row['total_votes']
  return False

# Helper functions for account generation

def generate_name( val ):

  #".12345abcdefghijklmnopqrstuvwxyz"

  str_idx_name = str( val )

  result = ""
  for c in str_idx_name:
    result += chr( int(c) + 97 )

  return result

def generateAccounts():
  random.seed( time.time() )

  #searching 10 times not existing accounts
  for i in range( 0, 10 ):
    val_owner = random.randint( 10000, 10000000000 )

    #limit - only 12 chars
    val_new_account = random.randint( 100000000000, 999999999999 )

    #creating names according to EOS rules
    owner = generate_name( val_owner )
    new_account = generate_name( val_new_account )

    #checking if newly created names exist
    if validateAccount( owner, False ) and validateAccount( new_account, False ):
      break

  return owner, new_account

# Actions and tests

def makeManyAccounts(accounts_number):
  for x in range(accounts_number):
    owner, new_account = generateAccounts()
    run(args.cleos +' --url http://%s:%s system newaccount beos.gateway %s %s %s --transfer-ram' % (args.nodeos_ip, args.nodeos_port, new_account, owner_key, active_key ) )
    accounts_names.append(new_account)
    if not validateAccount( new_account, True ):
      return False

  return True

def fillAccountsWithBeos(proxy_value):
  for x in range(len(accounts_names)):
    run(args.cleos +' --url http://%s:%s push action beos.gateway issue \'[ "%s", "%s PXBTS", "MEMO" ]\' -p beos.gateway ' % (args.nodeos_ip, args.nodeos_port, accounts_names[x], proxy_value ) )
    if not validateIssue(accounts_names[x], True ):
      return False
  return True

def changeParams(block):
  try:
    shift = 5
    start = block + shift
    end = start + 1 # number of rewards: 1
    interval = 10

    params_str = '[ [ [ %i, %i, %i, %i, 0 ],[ %i, %i, %i, %i, 0 ], ["0.0000 PXBTS"], 10000 ] ]' % ( start, start, end, interval, start, start, end, interval )
    run(args.cleos +' --url http://%s:%s push action beos.distrib changeparams \'%s\' -p beos.distrib ' % (args.nodeos_ip, args.nodeos_port, params_str ) )  
  except Exception as _ex:
    print('[ERROR] in changeParams', _ex)
    return False
  return True

def regProducers(producers_quantity):
  for x in range(producers_quantity):
    account = accounts_names[x]
    url = 'http://%s.com' % account
    run(args.cleos +' --url http://%s:%s system regproducer %s %s %s %s' % (args.nodeos_ip, args.nodeos_port, account, owner_key, url, 0 ) )
    producers_names.append(account)
  return True

def voteProducer(voter_name, producers_names):
  producers_string = ''
  for producer in producers_names:
    producers_string += (producer + ' ')
  run(args.cleos +' --url http://%s:%s system voteproducer prods %s %s' % (args.nodeos_ip, args.nodeos_port, voter_name, producers_string ) )
  return producers_string

def voteTest():
  voted_producers = [
    producers_names[0], producers_names[1], producers_names[2], producers_names[3],
    producers_names[10], 'eosio', producers_names[16], producers_names[17], producers_names[18],
    producers_names[19]
  ]
  try:
    print("[INFO] one voter for many producers")
    test_array = [voted_producers[0], voted_producers[1], voted_producers[2], voted_producers[3]]
    voteProducer(producers_names[4], test_array)
    print("[INFO] many voter for one producer")
    voteProducer(producers_names[5], [voted_producers[4]])
    voteProducer(producers_names[7], [voted_producers[4]])
    voteProducer(producers_names[8], [voted_producers[4]])
    voteProducer(producers_names[6], [voted_producers[4]])
    print("[INFO] votes for eosio")
    voteProducer(producers_names[9], [voted_producers[5]])
    voteProducer(producers_names[11], [voted_producers[5]])
    print("[INFO] few 1 for 1 votes")
    for i in range(4):
      voteProducer(producers_names[12 + i], [voted_producers[6 + i]])

    # Check if votes was correct
    ret = True
    for voted_producer in voted_producers:
      if checkVotesForProducer(voted_producer) == '0.00000000000000000':
        print('[ERROR] vote for user %s did not work' % (voted_producer))
        ret = False
    if checkVotesForProducer(producers_names[4]) != '0.00000000000000000':
      print('[ERROR] user %s should not have votes' % (producers_names[4]))
      ret = False
    return ret
  except Exception as _ex:
    print('[ERROR] in changeParams', _ex)
    return False

def voteproducerUnapprove(voter_name, producer_name):
  run(args.cleos +' --url http://%s:%s system voteproducer unapprove %s %s' % (args.nodeos_ip, args.nodeos_port, voter_name, producer_name ) )

def unregprod(producer_name):
  try:
    run(args.cleos +' --url http://%s:%s system unregprod %s' % (args.nodeos_ip, args.nodeos_port, producer_name ) )
    return True

  except Exception as _ex:
    print('[ERROR] in changeParams', _ex)
    return False

def tryVoteUnregistered():
  voter_name = producers_names[21]
  unregistered_producer_name = producers_names[20]
  try:
    print('[INFO] Vote unregistered producer, expected error')
    voteProducer(voter_name, [unregistered_producer_name])
    vote_weight = getAccountData(unregistered_producer_name)['voter_info']['last_vote_weight']
    if vote_weight != '0.00000000000000000':
      return False
    else:
      return True
  except Exception as _ex:
    print('[ERROR] in changeParams after unregprod', _ex)
    return False

def tryVoteNotProducer():
  voter_name = accounts_names[50]
  not_producer_name = accounts_names[51]
  try:
    print('[INFO] Vote normal user, not producer, expected error')
    voteProducer(voter_name, [not_producer_name])
    vote_weight = getAccountData(not_producer_name)['voter_info']['last_vote_weight']
    if vote_weight != '0.00000000000000000':
      return False
    else:
      return True
  except Exception as _ex:
    print('[ERROR] in changeParams unregistered user', _ex)
    return False

def unregprodTest():
  unregprod(producers_names[5])
  unregprod(producers_names[16])
  unregprod(producers_names[20])
  if isProducerRegistered(producers_names[5]) or isProducerRegistered(producers_names[16]) or isProducerRegistered(producers_names[20]):
    return False
  else:
    return True

def unapproveTest():
  test_voters = [producers_names[13], producers_names[5], producers_names[4]]
  test_producers = [producers_names[17], producers_names[10], producers_names[0]]
  for i in range(len(test_voters)):
    vote_before = checkVotesForProducer(test_producers[i])
    voteproducerUnapprove(test_voters[i], test_producers[i])
    if checkVotesForProducer(test_producers[i]) == vote_before:
      return False
  return True

# Command Line Arguments
parser = argparse.ArgumentParser()

parser.add_argument('--gateway-private-key', metavar='', help="BEOS.GATEWAY Private Key", default='5Ka14byMGwBqE4Q149pffSjXf547otfZ1NKdTEq1ivwg9DjMoi6', dest="gateway_private_key")
parser.add_argument('--public-key', metavar='', help="EOSIO Public Key", default='EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV', dest="public_key")
parser.add_argument('--private-Key', metavar='', help="EOSIO Private Key", default='5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3', dest="private_key")
parser.add_argument('--nodeos-ip', metavar='', help="Ip address of nodeos and keosd", default='127.0.0.1', dest="nodeos_ip")
parser.add_argument('--nodeos-port', metavar='', help="Port", default=8888, dest="nodeos_port")
parser.add_argument('--main-dir', metavar='', help="Main dictory for: cleos, nodeos, keosd", default='')
parser.add_argument('--cleos', metavar='', help="Cleos command", default='programs/cleos/cleos ')
parser.add_argument('--wallet-dir', metavar='', help="Path to wallet directory", default='./wallet/')

if __name__ == "__main__":
  args = parser.parse_args()
  args.cleos = args.main_dir + "/" + args.cleos

  accounts_number = 80
  producers_number = 40

  try:
    stepStartWallet()
    print(datetime.datetime.now(), '[ACTION] create account and make issues with PXBTS to them')
    if makeManyAccounts(accounts_number):
      print('[OK] Create accounts - test passed')
    else:
      print('[ERROR] Create accounts - test failed')
    if fillAccountsWithBeos('1.0000'):
      print('[OK] Issues - test passed')
    else:
      print('[ERROR] Issues - test failed')
  
    print(datetime.datetime.now(), '[ACTION] set rewards distribution')
    block = getBlock()
    print("[INFO] distribution in block %s" % ( block ) )
    if changeParams(block):
      print('[OK] succesfully pushed changeParams action')
    else:
      print('[ERROR] changeParams action failed')

    time.sleep(3) # =======

    print(datetime.datetime.now(), '[ACTION] set rewards distribution')
    regProducers(producers_number)

    time.sleep(1) # ========

    if validateProducersQuantity():
      print('[OK] producers registered')
    else:
      print('[ERROR] mismatch in producents quantity after registration')

    print(datetime.datetime.now(), '[ACTION] make voting for few producers')
    if voteTest():
      print('[OK] vote test passed')
    else:
      print('[ERROR] in voting')

    time.sleep(1) # ========

    print(datetime.datetime.now(), '[ACTION] unregister some producer')
    if unregprodTest():
      print('[OK] unregprod test passed')
    else:
      print('[ERROR] in unregprod')

    time.sleep(1) # ========

    print(datetime.datetime.now(), '[ACTION] try to vote for unregistered producer')
    if tryVoteUnregistered():
      print('[OK] imposible to vote for unregistered producer')
    else:
      print('[ERROR] in voting for unregistered producer')

    print(datetime.datetime.now(), '[ACTION] try to vote for normal user (not producer)')
    if tryVoteNotProducer():
      print('[OK] imposible to vote for not producer account')
    else:
      print('[ERROR] in voting not producer account')

    time.sleep(1) # ========

    print(datetime.datetime.now(), '[ACTION] test of voteproducer unapprove cleos command')
    if unapproveTest():
      print('[OK] voteproducer unapprove works properly')
    else:
      print('[ERROR] in voteproducer unapprove')
    

  except Exception as _ex:
    print("[ERROR] Exception `%s` occured while executing test07 ."%(str(_ex)))

