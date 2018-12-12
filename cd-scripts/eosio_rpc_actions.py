#!/usr/bin/python3

import logging
import json
import sys
import datetime

import eosio_tools
import eosio_rpc_client

try:
    import config
except Exception as ex:
    msg = "config.py is not present. Please make a copy of config-example.py and name it as config.py. Edit config.py to customize your build environment."
    print(msg)

MODULE_NAME = "EOSIO RPC Actions Py"
logger = logging.getLogger(MODULE_NAME)
logger.setLevel(config.LOG_LEVEL)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(config.LOG_LEVEL)
ch.setFormatter(logging.Formatter(config.LOG_FORMAT))

fh = logging.FileHandler(config.MAIN_LOG_PATH)
fh.setLevel(config.LOG_LEVEL)
fh.setFormatter(logging.Formatter(config.LOG_FORMAT))

logger.addHandler(ch)
logger.addHandler(fh)

EOSIO = eosio_rpc_client.eosio_rpc_client.EosioInterface(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT)

def extend_expiration_time(_time, _extend_by_seconds = 60):
  format = "%Y-%m-%dT%H:%M:%S.%f"
  d = datetime.datetime.strptime(_time, format)
  d = d + datetime.timedelta(seconds = _extend_by_seconds)
  return datetime.datetime(d.year, d.month, d.day, d.hour, d.minute , d.second).strftime(format)

def unlock_wallet(wallet_name, wallet_password):
  data = [wallet_name, wallet_password]
  EOSIO.wallet.unlock(data)

def import_key(wallet_name, key):
  data = [wallet_name, key]
  EOSIO.wallet.import_key(data)

def create_wallet():
  ret = EOSIO.wallet.create(config.MASTER_WALLET_NAME)
  with open(config.WALLET_PASSWORD_PATH, "w") as f:
    f.write("{0}\n".format(ret))
  for key in config.SYSTEM_ACCOUNT_KEYS:
        import_key(config.MASTER_WALLET_NAME, key)

def create_account(creator, name, owner_key, active_key):
  create_acnt_data = {
    "creator": creator,
    "name": name,
    "init_ram":True,
    "owner": {
      "threshold": 1,
      "keys": [{
          "key": owner_key,
          "weight": 1
        }
      ],
      "accounts": [],
      "waits": []
    },
    "active": {
      "threshold": 1,
      "keys": [{
          "key": active_key,
          "weight": 1
        }
      ],
      "accounts": [],
      "waits": []
    }
  }

  push_action(creator, "newaccount", create_acnt_data, creator)

def push_action(account, action, data, permission):
  actions = []
  abi_to_json_bin_resp = EOSIO.chain.abi_json_to_bin(data)
  actions.append({ 
    "account": account,
    "name":  action,
    "authorization": [{ 
      "actor" : account,
      "permission": permission
    }],
    "data" : abi_to_json_bin_resp["binargs"]
  })

  get_info_resp = EOSIO.chain.get_info()
  get_block_resp = EOSIO.chain.get_block(get_info_resp["head_block_num"])
  public_keys_resp = EOSIO.wallet.get_public_keys()

  get_required_key_data = {
    "available_keys" : public_keys_resp,
    "transaction":{
      "actions": actions, 
      "context_free_actions": [],
      "context_free_data": [],
      "delay_sec": 0,
      "expiration": extend_expiration_time(get_block_resp["timestamp"]),
      "max_kcpu_usage": 0,
      "max_net_usage_words": 0,
      "ref_block_num": get_block_resp["block_num"],
      "ref_block_prefix": get_block_resp["ref_block_prefix"],
      "signatures": []
    }
  }

  get_required_key_resp = EOSIO.chain.get_required_key(get_required_key_data)

  sign_transaction_data = [
    {
      "ref_block_num":get_block_resp["block_num"],
      "ref_block_prefix":get_block_resp["ref_block_prefix"],
      "expiration" : extend_expiration_time(get_block_resp["timestamp"]),
      "actions" : actions,  
      "signatures":[],
    },
    get_required_key_resp["required_keys"],
    get_block_resp["chain_id"]
  ]

  sign_transaction_resp = EOSIO.chain.sign_transaction(sign_transaction_data)

  push_transaction_data = {
    "compression": "none",
    "transaction": {
      "expiration": sign_transaction_resp["expiration"],
      "ref_block_num": sign_transaction_resp["ref_block_num"],
      "ref_block_prefix": sign_transaction_resp["ref_block_prefix"],
      "context_free_actions": [],
      "actions" : actions,
      "transaction_extensions": []
    },
    "signatures": sign_transaction_resp["signatures"]
  }

  push_transaction_resp = EOSIO.chain.push_transaction(push_transaction_data)
  if "transaction_id" in push_transaction_resp:
    logger.info("[ACTION][OK] {0} pushed to block {1}".format(actions, push_transaction_resp["processed"]["block_num"]))
  else:
    logger.error("[ACTION][ERROR] failed to push action {0} to block".format(actions))


def set_contract(account, contract, permission):
  pass

def get_balance(account_name, currency):
  data = {"code" : "eosio.token", "account" : account_name, "symbol" : currency}
  ret = EOSIO.chain.get_currency_balance(data)
  if ret and isinstance(ret, list):
    ret = ret[0].split()[0]
    return float(ret)
  return 0.

def get_account(account_name):
  data = {"account_name" : account_name}
  ret = EOSIO.chain.get_account(data)
  logger.info(json.dumps(ret, indent = 2, separators = (',', ': ')))