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
import threading

class colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

STARTING_USERS            = 15
STARTING_ISSUES           = 10
PRODUCERS_DURING_REWARDS  = 2
PRODUCERS_BEFORE_REWARDS  = 1
REWARDS                   = True

args                      = None
users_with_balance        = []
users_without_balance     = []
producers                 = ['eosio']
votes                     = [0] * (PRODUCERS_DURING_REWARDS + len(producers))

def run(args):
  print(' test08:', args)
  subprocess.call(args, shell=True)

def importKeys():
  run(args.cleos +'wallet import -n default-test08 --private-key ' + args.private_key)
  run(args.cleos +'wallet import -n default-test08 --private-key ' + args.gateway_private_key)

def startWallet():
  run('rm -f ' + "~/eosio-wallet/default-test08.wallet" )
  run('rm -rf ' + os.path.abspath(args.wallet_dir))
  run('mkdir -p ' + os.path.abspath(args.wallet_dir))
  time.sleep(.4)
  run(args.cleos + 'wallet create -n default-test08 --to-console' )

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

def changeParams( block ) :

  shift = 5
  start = block + shift
  end = start + 5 # number of rewards: 3
  interval = 5

  print(colors.BLUE + "===== Setting change params =====")

  params_str = '[ [ [ %i, %i, %i, %i, 1000000 ],[ 10000000, 10000000, 10000005, 20, 0 ], ["0.0000 PXBTS"], 10000 ] ]' % ( start, start, end, interval )
  run(args.cleos +' --url http://%s:%s push action beos.distrib changeparams \'%s\' -p beos.distrib ' % (args.nodeos_ip, args.nodeos_port, params_str ) )

  return start, end

def getBlock():
  data = {}
  res = askServer(data, 'chain/get_info')
  return res['head_block_num']

def validateVotes():
  values = []
  data = {"json": "true"}
  res = askServer(data, 'chain/get_producers')
  if res['rows']:
    rows = res['rows']
  for row in rows:
    values.append({ 'name': row['owner'], 'value': row['total_votes'].split('.')[0] })

  total_votes_req = 0
  for i in range(0, len(values)):
    total_votes_req = total_votes_req + int(values[i]['value'])

  for value in values:
    value['percentage'] = round(int(value['value']) / total_votes_req, 4)

  total_votes = 0
  for i in range(0, len(votes)):
    total_votes = total_votes + votes[i]

  percentages = []
  for vote in votes:
    percentages.append(round(vote / total_votes, 4))

  for i in range(0, len(producers)):
    if int(percentages[i]) == int(values[i]['percentage']):
      print(colors.GREEN + 'Votes for %s are as expected' % (producers[i]) + colors.ENDC)
    else:
      print(colors.FAIL + 'Votes are not as expected' + colors.ENDC)
      exit()

def validateAccount(_name, _isValid):
  data = {"account_name":_name}
  res = askServer(data, 'beos/address_validator')
  if res['is_valid'] != _isValid:
    return False
  else:
    return True

def validateBalance(_user):
  data = {"code": "eosio.token", "account": _user, "symbol": "PXBTS"}
  res = askServer(data, 'chain/get_currency_balance')
  return res

def validateProducers(expected_number):
  data = {}
  res = askServer(data, 'chain/get_producers')
  if (res["rows"]):
    if (len(res["rows"]) - 1 == expected_number):
      print(colors.GREEN + "Number of producers is as expected" + colors.ENDC)
    else:
      print(res["rows"])
      print(colors.FAIL + "Number of producers is not as expected %s but is %s" % ( expected_number, len(res["rows"]) - 1 ) + colors.ENDC)
      exit()

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
    #limit - only 12 chars
    val_new_account = random.randint( 100000000000, 999999999999 )

    #creating names according to EOS rules
    new_account = generate_name( val_new_account )

    #checking if newly created names exist
    if validateAccount( new_account, False ):
      break

  return new_account

def createAccount():
  active_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"

  new_account = generateAccounts()

  print(colors.BLUE + "===== Creating account: %s =====" % ( new_account ) + colors.ENDC)

  run(args.cleos + ' --url http://%s:%s create account beos.gateway %s %s %s --transfer-ram' % (args.nodeos_ip, args.nodeos_port, new_account, args.public_key, args.public_key ) )
  ret = validateAccount( new_account, True )
  if (ret):
    print(colors.GREEN + "Created account: %s" % ( new_account ) + colors.ENDC)
    users_without_balance.append(new_account)
  else:
    print(colors.FAIL + "Error in creating account: %s" % ( new_account ) + colors.ENDC)
    exit()

def giveIssue():
  number = random.randint(0, len(users_without_balance) - 1)
  user = users_without_balance[number]
  amount = "5.0000 PXBTS"

  print(colors.BLUE + "===== Giving issue to account: %s =====" % ( user ) + colors.ENDC)

  run(args.cleos + " --url http://%s:%s push action beos.gateway issue \'{\"memo\": \"\", \"to\": \"%s\", \"quantity\": \"%s\"}\' -p beos.gateway@active" % ( args.nodeos_ip, args.nodeos_port, user, amount ))

  res = validateBalance(user)
  if (len(res) != 0):
    if (res[0] == amount):
      print(colors.GREEN + "Issue done for user %s with value %s" % ( user, amount ))
      users_with_balance.append(user)
      del users_without_balance[number]
    else:
      print(colors.FAIL + "Amount %s is bad" % ( res[0] ))
      exit()
  else:
    print(colors.FAIL + "No balance")
    exit()

def voteProducer(number_of_voters):
  if number_of_voters == 'all':
    to_vote = users_with_balance
  else:
    to_vote = users_with_balance[:number_of_voters]

  number = random.randint(1, len(producers) - 1)
  producer = producers[number]

  for voter in to_vote:
    print(colors.BLUE + "==== Voting on producer %s by user %s" % ( producer, voter ) + colors.ENDC)
    run(args.cleos + " --url http://%s:%s system voteproducer approve %s %s" % ( args.nodeos_ip, args.nodeos_port, voter, producer ))
  print(votes[number])
  votes[number] = len(to_vote) + votes[number]

def voteEosio():
  voters = producers[1:] + users_with_balance
  producer = 'eosio'

  for voter in voters:
    print(colors.BLUE + "==== Voting on producer %s by user %s" % ( producer, voter ) + colors.ENDC)
    run(args.cleos + " --url http://%s:%s system voteproducer approve %s %s" % ( args.nodeos_ip, args.nodeos_port, voter, producer ))
  votes[0] = len(voters)

def checkVotes():
  validateVotes()


def registerProducer(status):
  active_key = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"

  number = random.randint(0, len(users_with_balance) - 1)
  user = users_with_balance[number]
  print(colors.BLUE + "===== Registering producer for user %s during rewards =====" % ( user ) + colors.ENDC)

  run(args.cleos + " --url http://%s:%s system regproducer %s %s" % ( args.nodeos_ip, args.nodeos_port, user, active_key ))

  if status:
    producers.append(user)
    del users_with_balance[number]

def createAccounts(number):
  for i in range( 0, number ):
    createAccount()

def giveIssues(number):
  for i in range( 0, number ):
    res = giveIssue()
  return True

def registerProducers(number, status):
  for i in range( 0, number ):
    registerProducer(status)

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

  try:
    stepStartWallet()
    createAccounts(STARTING_USERS)
    i_res = giveIssues(STARTING_ISSUES)

    if (i_res):
      block = getBlock()
      startblock, endblock = changeParams(block)
      registerProducers(PRODUCERS_BEFORE_REWARDS , False)
      validateProducers(0)
      while (REWARDS):
        if (getBlock() == startblock):
          print(colors.BLUE + "Start of rewards")
        if (getBlock() > startblock and len(producers) == 1):
          registerProducers(PRODUCERS_DURING_REWARDS, True)
          validateProducers(PRODUCERS_DURING_REWARDS)
          voteEosio()
          voteProducer('all')
          checkVotes()
        if (getBlock() >= endblock):
          print(colors.BLUE + "End of rewards")
          REWARDS = False
        time.sleep(.5)

    print(colors.BOLD + "Users without balance: %s" % ( users_without_balance ))
    print("Users with balance: %s" % ( users_with_balance ))
    print("Producers: %s" % ( producers ))
    print("Votes: %s" % ( votes ) + colors.ENDC)

  except Exception as _ex:
    print("[ERROR] Exception `%s` occured while executing test08 ."%(str(_ex)))

