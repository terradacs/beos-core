#!/usr/bin/python3
import eosio_actions
import json

# This is helper script for adding new tokens. 
# Usage:
# 
# ./add_token.py --total-supply 10000000000.0000 --token-code TESTS --token-description tests
#
# Default values are:
# --total-supply 10000000000.0000
# --token-code BTSMD
# --token-description btsmd
#
# So it is possible to use this script simply by calling:
# ./add_token.py
# this call is equall calling:
# ./add_token.py --total-supply 10000000000.0000 --token-code BTSMD --token-description btsmd
#

if __name__ == "__main__":
  import argparse
  description = "This is helper script for adding new tokens. Usage: ./add_token.py --total-supply 10000000000.0000 --token-code TESTS --token-description tests"
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument("--total-supply", dest="total_suply", default="10000000000.0000", type=str, help="Total supply of the token (without code)")
  parser.add_argument("--token-code", dest="token_code", default="BTSMD", type=str, help="Token code")
  parser.add_argument("--token-description", dest="token_description", default="btsmd", type=str, help="Token description")

  args = parser.parse_args()
  try:
    #./cleos push action eosio.token create '["beos.gateway", "10000000000.0000 BTSMD"]' -p eosio.token
    eosio_actions.push_action("eosio.token", "create", '[ "beos.gateway", "{0} {1}"]'.format(args.total_suply, args.token_code), "eosio.token")
    
    #./cleos get table beos.gateway beos.gateway gatewaystate
    output = eosio_actions.get_table('beos.gateway', 'beos.gateway', 'gatewaystate')
    new_params = None
    if 'rows' in output:
      if len(output['rows']) > 0 and 'proxy_assets' in output['rows'][0]:
        new_params = output['rows'][0]
        new_params['proxy_assets'].append({'proxy_asset' : '{} {}'.format(args.total_suply, args.token_code), 'description' : '{}'.format(args.token_description)})

    #./cleos push action beos.gateway changeparams '{"new_params": {"proxy_assets":[{"proxy_asset":"10000000000.0000 BTS","description":"bts"},{"proxy_asset":"10000000000.0000 BRNP","description":"brownie.pts"},{"proxy_asset":"10000000000.0000 EOS","description":"eos"},{"proxy_asset":"10000000000.0000 BTSMD","description":"btsmd"}]} }' -p beos.gateway
    eosio_actions.push_action("beos.gateway", "changeparams", '{{"new_params": {0}}}'.format(json.dumps(new_params)), "beos.gateway")
  except Exception as ex:
    print("Error during upgrade {}".format(ex))