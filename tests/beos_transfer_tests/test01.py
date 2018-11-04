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
import threading
import requests
from functools import partial
from concurrent.futures import ThreadPoolExecutor

args = None
worker_start = True

def run(args):
    if subprocess.call(args, shell=True):
      sys.exit(1)

def background(args, is_pipe = False ):
  if is_pipe:
    return subprocess.Popen( args, stdout=subprocess.PIPE, shell=True )
  else:
    return subprocess.Popen( args, shell=True )

def prepare_file_start( actual_path ):
  run('rm -f ' + actual_path )
  f = open( actual_path, 'a' )
  f.write('{ \"result\": [ ')
  return f

def prepare_file_end( actual_file ):
  actual_file.write(' ]}')
  actual_file.close()

def extract_account( results ):
  return results[ len( results ) - 1 ][0]

def extract_balance( result ):
  return ""

def write_account( item ):
  return json.dumps( item )

def write_balance( account, name, item ):

  if args.allow_zero:
    result = " [ %s, \"%s\", \"%s\" ]" % ( item["amount"], name, account )
  else:
    amount = float( item["amount"] )
    if amount == 0:
      result = ""
    else:
      result = " [ %s, \"%s\", \"%s\" ]" % ( item["amount"], name, account )

  return result

def _evaluate( return_callable, write_callable, _file, out, start, try_decode ):
    if try_decode:
      str_response = out.decode('UTF-8')
      json_out = json.loads( str_response )
      results = json_out['result']
    else:
      results = out['result']

    for item in results:
      data = write_callable( item )
      if len( data ) > 0 :
        if start:
          _file.write( data )
        else:
          _file.write( ',' +  data )
      start = False

    return1 = return_callable( results )
    return start, return1

def evaluate( return_callable, write_callable, _file, pipe, start ):
  try:

    out, err = pipe.communicate()
    _start, _result = _evaluate( return_callable, write_callable, _file, out, start, True )
    return _start, _result, False

  except Exception as e:
    print( "\nSomething went wrong during response evaluation: (", e, ")\n" )

  return '', False, True

def create_command( action, account, detail, only_param = False ):
  command_data = "{\"jsonrpc\":\"1.0\",\"id\":\"666\",\"method\":\"%s\",\"params\":[\"%s\",%s] }" % ( action, account, detail )
  if only_param:
    return command_data
  return "curl --data-binary '%s' -H content-type:text/plain %s " % ( command_data, server )

def _lookup_accounts( account_file ):
  current_account = ""
  limit = 1000
  total_limit = 0
  start = True
  action = "lookup_accounts"

  if limit > args.limit and args.limit != 0:
    limit = args.limit

  while True:
    total_limit += limit
    start, last_account, error = evaluate( extract_account, write_account, account_file, background( create_command( action, current_account, limit ), True ), start )

    account_file.flush()
    os.fsync( account_file.fileno() )

    if current_account == last_account or ( total_limit >= args.limit and args.limit != 0 ) or error:
      break

    current_account = last_account

def lookup_accounts():
  f = prepare_file_start( args.accounts_file_path )
  _lookup_accounts( f )
  prepare_file_end( f )

def worker( params ):
  try:

    _server = "http://" + server
    json_rpc_headers = {"content-type": "application/json"}

    response = requests.post( _server, data=params, headers=json_rpc_headers )
    response_json = response.json()

    if response_json.get("error"):
      print('This is error with %s query' % params )
    else:
      print( response_json )

    return response_json
  
  except Exception as e:
    print( "\nSomething went wrong during thread-response evaluation: (", e, ")\n" )

def _get_account_balances( account_file, balance_file ):
  start = True
  action = "get_account_balances"
  asset = '[\"1.3.0\"]'

  account_file = open( account_file )
  res = json.load( account_file )
  accounts = res[ "result" ]

  idx = 0
  futures = []
  bounds = []
  done = False
  start = True

  buffer_length = 100

  while True:
    with ThreadPoolExecutor( max_workers = args.threads ) as executor:
      for i in range( args.threads ):

        if idx >= len( accounts ):
          done = True
          break

        item = accounts[ idx ]
        idx += 1

        current_name = item[0]
        current_account = item[1]

        command = create_command( action, current_account, asset, True )

        bound = partial( write_balance, current_account, current_name )
        bounds.append( bound )

        future = executor.submit( worker, command )
        futures.append( future )

      if ( idx % buffer_length ) == 0:
        for _tuple in zip( futures, bounds ):
          _evaluate( extract_balance, _tuple[1], balance_file, _tuple[0].result(), start, False )
          start = False
        futures = []
        bounds = []

    if done:
      break

  for _tuple in zip( futures, bounds ):
    _evaluate( extract_balance, _tuple[1], balance_file, _tuple[0].result(), start, False )
    start = False

def get_account_balances():
  f = prepare_file_start( args.balances_file_path )
  _get_account_balances( args.accounts_file_path, f )
  prepare_file_end( f )


#Arguments processing
parser = argparse.ArgumentParser()

parser.add_argument('--server', metavar='', help="Server", default='192.168.4.154')
parser.add_argument('--port', metavar='', help="Port", default='8000')
parser.add_argument('--server-witness', metavar='', help="Witness", default='graphene-witness/')
parser.add_argument('--accounts-file-path', metavar='', help="File with all accounts from bitshares blockchain", default='./bts_accounts.json')
parser.add_argument('--balances-file-path', metavar='', help="File with all balances from bitshares blockchain", default='./bts_balances.json')
parser.add_argument('--limit', metavar='', help="Limit", type=int, default=30 )
parser.add_argument('--threads', metavar='', help="Number of threads", type=int, default=30 )
parser.add_argument('--allow-zero', metavar='', help="Zero amount is allowed", type=int, default=1 )

args = parser.parse_args()
server = args.server + ':' + args.port + '/' + args.server_witness

args = parser.parse_args()

lookup_accounts()
get_account_balances()

