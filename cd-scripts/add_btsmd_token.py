#!/usr/bin/python3
import eosio_actions
import json

# This is helper script for adding new tokens. 
# Usage:
# 
# ./add_token.py --total-supply 10000000000.0000
#
# Default values are:
# --total-supply 10000000000.0000
#
# So it is possible to use this script simply by calling:
# ./add_token.py
# this call is equall calling:
# ./add_token.py --total-supply 10000000000.0000
#

if __name__ == "__main__":
  import argparse
  description = "This is helper script for adding new tokens. Usage: ./add_token.py --total-supply 10000000000.0000"
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument("--total-supply", dest="total_suply", default="10000000000.0000", type=str, help="Total supply of the token (without code)")

  args = parser.parse_args()
  try:
    #./cleos push action eosio.token create '["beos.gateway", "10000000000.0000 BTSMD"]' -p eosio.token
    eosio_actions.push_action("eosio.token", "create", '[ "beos.gateway", "{0} BTSMD"]'.format(args.total_suply), "eosio.token")
    
    new_params = {
      "proxy_assets" : [
        {
          "proxy_asset" : "10000000000.0000 BTS", # maximum amount that will ever be allowed to be issued (must cover all BTS)
          "description" : "bts"
        },
        {
          "proxy_asset" : "10000000000.0000 BRNP", # maximum amount that will ever be allowed to be issued (must cover all Brownie.PTS)
          "description" : "brownie.pts"
        },
        {
          "proxy_asset" : "10000000000.0000 EOS", # maximum amount that will ever be allowed to be issued (must cover all EOS)
          "description" : "eos"
        },
        {
          'proxy_asset' : '{} BTSMD'.format(args.total_suply), 
          'description' : 'btsmd'
        }
      ]
    }

    #./cleos push action beos.gateway changeparams '{"new_params": {"proxy_assets":[{"proxy_asset":"10000000000.0000 BTS","description":"bts"},{"proxy_asset":"10000000000.0000 BRNP","description":"brownie.pts"},{"proxy_asset":"10000000000.0000 EOS","description":"eos"},{"proxy_asset":"10000000000.0000 BTSMD","description":"btsmd"}]} }' -p beos.gateway
    eosio_actions.push_action("beos.gateway", "changeparams", '{{"new_params": {0}}}'.format(json.dumps(new_params)), "beos.gateway")
  except Exception as ex:
    print("Error during upgrade {}".format(ex))