#!/usr/bin/env python3

import sys
import requests
import argparse
import logging

MODULE_NAME = "EOS-Voter RPC Test"
FORMAT = '%(asctime)-15s -- %(levelname)s -- %(message)s'
logging.basicConfig(format = FORMAT, level=logging.INFO)

#Here are RPC methods which shall be user at tests: 
#status code: 200 OK
#http://192.168.4.208:8888/v1/chain/get_info
#http://192.168.4.208:8888/v1/chain/get_account - {account_name: "account"}
#http://192.168.4.208:8888/v1/chain/get_currency_balance - {account: "account", code: "eosio.token", symbol: "BEOS"}
#http://192.168.4.208:8888/v1/chain/get_table_rows - {code: "eosio", json, limit, scope: "eosio", table: "producers"}
#http://192.168.4.208:8888/v1/chain/get_table_rows - {code: "eosio", json, limit, scope: "eosio", table: "global"}
#http://192.168.4.208:8888/v1/chain/get_currency_stats - {code, symbol}
#http://192.168.4.208:8888/v1/chain/get_table_rows - {code: "producerjson", json, limit, scope: "producerjson", table: "producerjson"}
#http://192.168.4.208:8888/v1/chain/get_table_rows - {code: "regproxyinfo", json, limit, scope: "regproxyinfo", table: "proxies"}

#Status code: 500 Internal Server Error
#http://192.168.4.208:8888/v1/chain/get_table_rows - {code: "anchorwallet", json, limit, scope: "anchorwallet", table: "constants"}

def send_request(url, payload = None):
  try:
    if payload is not None:
      return requests.get(url, json = payload)
    return requests.get(url)
  except Exception as ex:
    logging.error("Exception occurred during sending request: {0}".format(ex))
    sys.exit(1)

def get_info(nodeos_url):
  url = nodeos_url + "v1/chain/get_info"
  return send_request(url)

def get_account(nodeos_url, account_name):
  url = nodeos_url + "v1/chain/get_account"
  payload = {"account_name" : account_name}
  return send_request(url, payload)

def get_currency_balance(nodeos_url, account_name, symbol):
  url = nodeos_url + "v1/chain/get_currency_balance"
  payload = {"account": account_name, "symbol": symbol, "code":"eosio.token"}
  return send_request(url, payload)

def get_table_rows(nodeos_url, code, json, limit, scope, table):
  url = nodeos_url + "v1/chain/get_table_rows"
  payload = {"code": code, "json" : json, "limit" : limit, "scope": scope, "table": table}
  return send_request(url, payload)

def get_currency_stats(nodeos_url, code, symbol):
  url = nodeos_url + "v1/chain/get_currency_stats"
  payload = {"code" : code, "symbol" : symbol}
  return send_request(url, payload)

def check_response(response, expected_return_code, test_name):
  if response.status_code == expected_return_code:
    logging.info("[SUCCESS] {0} succeeded".format(test_name))
    return
  logging.error("[FAILED] {0} failed with ret code from response {1}".format(test_name, response.status_code))
  sys.exit(1)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--nodeos-ip', metavar='', help="Nodeos IP address", default='127.0.0.1', dest="nodeos_ip")
  parser.add_argument('--nodeos-port', metavar='', help="Nodeos port", default='8888', dest="nodeos_port")
  parser.add_argument('--account-for-get-account-test', metavar='', help="Account name for get_account test", default='eosio', dest='account_get_account')
  parser.add_argument('--account-for-get-currency-balance', metavar='', help="Account name for get_currency_balance test", default='eosio.token', dest="account_get_currency")
  parser.add_argument('--symbol-for-get-currency-balance', metavar='', help="Symbol for get_currency_balance test", default='BEOS', dest="symbol_get_currency")
  parser.add_argument('--code-for-get-currency-stats', metavar='', help="Code for get_currency_stats test", default='eosio.token', dest="code_get_currency_stats")
  parser.add_argument('--symbol-for-get-currency-stats', metavar='', help="Symbol for get_currency_stats test", default='BEOS', dest="symbol_get_currency_stats")

  args = parser.parse_args()

  nodeos_url = "http://{0}:{1}/".format(args.nodeos_ip, args.nodeos_port)
  
  response = get_info(nodeos_url)
  check_response(response, 200, "get_info test")
  
  response = get_account(nodeos_url, args.account_get_account)
  check_response(response, 200, "get_account test - {0}".format(args.account_get_account))

  response = get_currency_balance(nodeos_url, args.account_get_currency, args.symbol_get_currency)
  check_response(response, 200, "get_currency_balance test")

  response = get_table_rows(nodeos_url, "eosio", True, 1000, "eosio", "producers")
  check_response(response, 200, "get_table_rows test - eosio producers")

  response = get_table_rows(nodeos_url, "eosio", True, 1000, "eosio", "global")
  check_response(response, 200, "get_table_rows test - eosio global")

  response = get_table_rows(nodeos_url, "producerjson", True, 1000, "producerjson", "producerjson")
  check_response(response, 200, "get_table_rows test - producerjson")

  response = get_table_rows(nodeos_url, "regproxyinfo", True, 1000, "regproxyinfo", "proxies")
  check_response(response, 200, "get_table_rows test - regproxyinfo")

  response = get_table_rows(nodeos_url, "anchorwallet", True, 1000, "anchorwallet", "constants")
  check_response(response, 500, "get_table_rows test - anchorwallet")


