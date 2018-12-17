#!/usr/bin/python3

import logging
import json
import sys
import datetime

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

EOSIO = eosio_rpc_client.EosioInterface(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT)

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

def create_account(creator, name, owner_key, active_key, blocking = False):
  create_acnt_data = {"newaccount" : {
    "code" : "eosio",
    "action" : "newaccount",
    "authorized_by" : creator,
    "args" : {
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
  }}

  push_action(creator, creator, create_acnt_data, "active", blocking)

def push_action(account, actor, action_data, permission, blocking = False):
  actions = []
  for action, data in action_data.items():
    abi_to_json_bin_resp = EOSIO.chain.abi_json_to_bin(data)
    logger.info("abi_to_json_bin_resp")
    logger.info(abi_to_json_bin_resp)
    actions.append({ 
      "account": account,
      "name":  action,
      "authorization": [{ 
        "actor" : actor,
        "permission": permission
      }],
      "data" : abi_to_json_bin_resp["binargs"]
    })

  get_info_resp = EOSIO.chain.get_info()
  logger.info("get_info_resp")
  logger.info(get_info_resp)

  get_block_data = {"block_num_or_id" : get_info_resp["head_block_num"]}
  get_block_resp = EOSIO.chain.get_block(get_block_data)
  logger.info("get_block_resp")
  logger.info(get_block_resp)

  public_keys_resp = EOSIO.wallet.get_public_keys()
  logger.info("public_keys_resp")
  logger.info(public_keys_resp)

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

  get_required_key_resp = EOSIO.chain.get_required_keys(get_required_key_data)
  logger.info("get_required_key_resp")
  logger.info(get_required_key_resp)

  sign_transaction_data = [
    {
      "ref_block_num":get_block_resp["block_num"],
      "ref_block_prefix":get_block_resp["ref_block_prefix"],
      "expiration" : extend_expiration_time(get_block_resp["timestamp"]),
      "actions" : actions,  
      "signatures":[],
    },
    get_required_key_resp["required_keys"],
    get_info_resp["chain_id"]
  ]

  sign_transaction_resp = EOSIO.wallet.sign_transaction(sign_transaction_data)
  logger.info("sign_transaction_resp")
  logger.info(sign_transaction_resp)

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
  logger.info("push_transaction_resp")
  logger.info(push_transaction_resp)
  if "transaction_id" in push_transaction_resp:
    processed_block_num = push_transaction_resp["processed"]["block_num"]
    logger.info("[ACTION][OK] {0} pushed to block {1}".format(actions, processed_block_num))
    if blocking:
      block_until_transaction_in_irreversible_block(push_transaction_resp['transaction_id'], processed_block_num)
  else:
    logger.error("[ACTION][ERROR] failed to push action {0} to block".format(actions))

def block_until_transaction_in_irreversible_block(transaction_id, block_num, timeout = 60.):
  logger.info("Block until transaction_id: {0} is in irreversible block {1}".format(transaction_id, block_num))
  import time
  step = 0.25
  timeout_cnt = 0.
  while True:
    last_irreversible_block_num = EOSIO.chain.get_info()['last_irreversible_block_num']
    if last_irreversible_block_num >= block_num:
      get_block_data = {"block_num_or_id" : block_num}
      get_block_resp = EOSIO.chain.get_block(get_block_data)
      logger.info("get_block_resp")
      logger.info(get_block_resp)
      return
    time.sleep(step)
    timeout_cnt = timeout_cnt + step
    if timeout_cnt > timeout:
      msg = "Timeout reached during block_until_transaction_in_irreversible_block"
      logger.error(msg)
      raise TimeoutError()

#TODO: Not working atm, cleos is using some sort of custom packing. Without that packing deployment for contracts via RPC will not work
def set_contract(account, actor, contract_dir_path, permission):
  import os
  norm_dir_path = os.path.normpath(contract_dir_path)
  if not os.path.exists(contract_dir_path):
    msg = "Contract dir does not exists"
    logger.error(msg)
    raise FileNotFoundError()

  contract_name = os.path.basename(norm_dir_path)

  abi_file_name = norm_dir_path + "/" + contract_name + ".abi"
  abi_binary_data = None
  if not os.path.exists(abi_file_name):
    msg = "ABI file does not exists"
    logger.error(msg)
    raise FileNotFoundError()

  wasm_file_name = norm_dir_path + "/" + contract_name + ".wasm"
  wasm_binary_data = None
  if not os.path.exists(wasm_file_name):
    msg = "WASM file does not exists"
    logger.error(msg)
    raise FileNotFoundError()
  
  import json
  import abi_def
  with open(abi_file_name, "r") as abi_file:
    abi_json = json.loads(abi_file.read())
    abi_binary_data = abi_def.Abi(abi_json).pack()

  with open(wasm_file_name, "br") as wasm_file:
    wasm_binary_data = wasm_file.read()

  set_contract_actions = {
    "setcode" : {
      "code" : "eosio",
      "action" : "setcode",
      "authorized_by" : "eosio",
      "args" : {
        "account" : actor,
        "vmtype" : 0,
        "vmversion" : 0,
        "code" : wasm_binary_data.hex()
      }
    },
    "setabi" : {
      "code" : "eosio",
      "action" : "setabi",
      "authorized_by" : "eosio",
      "args" : {
        "account" : actor,
        "abi" : abi_binary_data.hex()
      }
    }
  }

  push_action(account, actor, set_contract_actions, permission)

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