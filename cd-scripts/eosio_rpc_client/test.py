#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import eosio_rpc_client

if __name__ == '__main__':
  backend = eosio_rpc_client.EosioBackend("127.0.0.1", 8888, "127.0.0.1", 8900)
  ifce = eosio_rpc_client.EosioInterface(backend)

  print("Get Info test")
  resp = ifce.chain.get_info()
  print(resp)