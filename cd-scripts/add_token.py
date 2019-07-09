#!/usr/bin/python3
import eosio_actions
import json

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("total_suply", type=str, help="Total suply of the token (without code)")
  parser.add_argument("token_code", type=str, help="Token code")
  parser.add_argument("token_description", type=str, help="Token description")

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