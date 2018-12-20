#!/usr/bin/env python3

import config
import logging
import sys

MODULE_NAME = "EOSIO RPC Actions Test"

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

if __name__ == "__main__":
  try:
    import eosio_rpc_actions
    import eosio_runner
    import eosio_tools

    wallet_url = "http://{0}:{1}".format(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT)
    eosio_runner.run_keosd(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT, config.DEFAULT_WALLET_DIR, False, True)
    eosio_rpc_actions.create_wallet()
    eosio_runner.run_nodeos(config.START_NODE_INDEX, config.PRODUCER_NAME, config.EOSIO_PUBLIC_KEY)

    eosio_rpc_actions.create_account("eosio", "eosio.msig", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "eosio.names", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "eosio.saving", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "eosio.vpay", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "eosio.unregd", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)

    eosio_rpc_actions.create_account("eosio", "eosio.bpay", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)

    eosio_rpc_actions.create_account("eosio", "eosio.ram", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "eosio.ramfee", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "eosio.stake", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)

    eosio_rpc_actions.create_account("eosio", "eosio.token", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "beos.init", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "beos.trustee", config.TRUSTEE_OWNER_PUBLIC_KEY, config.TRUSTEE_ACTIVE_PUBLIC_KEY)

    eosio_rpc_actions.create_account("eosio", "producerjson", config.PRODUCERJSON_OWNER_PUBLIC_KEY, config.PRODUCERJSON_ACTIVE_PUBLIC_KEY)
    eosio_rpc_actions.create_account("eosio", "regproxyinfo", config.REGPROXYINFO_OWNER_PUBLIC_KEY, config.REGPROXYINFO_ACTIVE_PUBLIC_KEY)

    # create producer accounts
    for producer, data in config.PRODUCERS_ARRAY.items():
        logger.info("Creating producer account for: {0}".format(producer))
        eosio_rpc_actions.import_key(config.MASTER_WALLET_NAME, data["prv_owner"])
        eosio_rpc_actions.import_key(config.MASTER_WALLET_NAME, data["prv_active"])
        eosio_rpc_actions.create_account("eosio", producer, data["pub_owner"], data["pub_active"])

    eosio_rpc_actions.set_contract("eosio", "eosio.token", config.CONTRACTS_DIR + "/eosio.token", "active")

    action_data = {
      "create" : {
        "code" : "eosio.token",
        "action" : "create",
        "authorized_by" : "eosio.token",
        "args" : {
          "issuer" : "eosio",
          "maximum_supply" : "{0} {1}".format(config.CORE_TOTAL_SUPPLY, config.CORE_SYMBOL_NAME)
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "eosio.token", action_data, "active")

    action_data = {
      "create" : {
        "code" : "eosio.token",
        "action" : "create",
        "authorized_by" : "eosio.token",
        "args" : {
          "issuer" : "beos.gateway",
          "maximum_supply" : "{0} {1}".format(config.PROXY_TOTAL_SUPPLY, config.PROXY_ASSET_NAME)
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "eosio.token", action_data, "active")

    # set initial producers, setprods is in eosio.bios contract so we need to load it first
    logger.info("Setting initial producers via setprods")
    eosio_rpc_actions.set_contract("eosio", "eosio", config.CONTRACTS_DIR + "eosio.bios", "active")
    producers = [{"producer_name": config.PRODUCER_NAME, "block_signing_key": config.EOSIO_PUBLIC_KEY}]
    if config.PRODUCERS_ARRAY:
        for producer, data in config.PRODUCERS_ARRAY.items():
            producers.append({"producer_name": producer, "block_signing_key": data["pub_active"]})
        import json


        action_data = {
          "setprods" : {
            "code" : "eosio",
            "action" : "setprods",
            "authorized_by" : "eosio",
            "args" : {"schedule" : producers}
          }
        }

        eosio_rpc_actions.push_action("eosio", "eosio", action_data, "active")

    # registering initial producers, regproducer is in eosio.system contract so it need to be loaded first
    eosio_rpc_actions.set_contract("eosio", "eosio", config.CONTRACTS_DIR + "eosio.system", "active")
    # special case, register eosio as producer
    action_data = {
      "regproducer" : {
        "code" : "eosio",
        "action" : "regproducer",
        "authorized_by" : "eosio",
        "args" : {
          "producer" : config.PRODUCER_NAME,
          "producer_key" : config.EOSIO_PUBLIC_KEY,
          "url" : "http://dummy.net",
          "location" : 0
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "eosio", action_data, "active")

    for producer, data in config.PRODUCERS_ARRAY.items():
        logger.info("Registering producer account for: {0}".format(producer))
        action_data = {
          "regproducer" : {
            "code" : "eosio",
            "action" : "regproducer",
            "authorized_by" : "eosio",
            "args" : {
              "producer" : producer,
              "producer_key" : data["pub_active"],
              "url" : data["url"],
              "location" : 0
            }
          }
        }
        eosio_rpc_actions.push_action("eosio", "eosio", action_data, "active")

    eosio_rpc_actions.set_contract("eosio", "beos.init", config.CONTRACTS_DIR + "eosio.init", "active")
    eosio_rpc_actions.set_contract("eosio", "beos.gateway", config.CONTRACTS_DIR + "eosio.gateway", "active")
    eosio_rpc_actions.set_contract("eosio", "beos.distrib", config.CONTRACTS_DIR + "eosio.distribution", "active")
    eosio_rpc_actions.set_contract("eosio", "producerjson", config.CONTRACTS_DIR + "producerjson", "active")
    eosio_rpc_actions.set_contract("eosio", "regproxyinfo", config.CONTRACTS_DIR + "proxyinfo", "active")

    action_data = {
      "initialissue" : {
        "code" : "eosio",
        "action" : "initialissue",
        "authorized_by" : "eosio",
        "args" : {
          "quantity" : config.CORE_INITIAL_SUPPLY,
          "min_activated_stake_percent" : config.MIN_ACTIVATED_STAKE_PERCENT
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "eosio", action_data, "active")
    
    action_data = {
      "initresource" : {
        "code" : "eosio",
        "action" : "initresource",
        "authorized_by" : "eosio",
        "args" : {
          "receiver" : "beos.gateway",
          "bytes" : config.GATEWAY_INIT_RAM,
          "stake_net_quantity" : config.GATEWAY_INIT_NET,
          "stake_cpu_quantity" : config.GATEWAY_INIT_CPU
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "eosio", action_data, "active")
    # eosio.get_account("eosio")
    # eosio.get_account("beos.gateway")

    action_data = {
      "initresource" : {
        "code" : "eosio",
        "action" : "initresource",
        "authorized_by" : "eosio",
        "args" : {
          "receiver" : "beos.distrib",
          "bytes" : config.DISTRIB_INIT_RAM,
          "stake_net_quantity" : -1,
          "stake_cpu_quantity" : -1
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "eosio", action_data, "active")
    # eosio.get_account("eosio")
    # eosio.get_account("beos.distrib")
    balance = eosio_rpc_actions.get_balance("eosio", config.CORE_SYMBOL_NAME)
    balance_int = int(balance * (10 ** config.CORE_SYMBOL_PRECISION) - config.DISTRIB_NETCPU_LEFTOVER)
    
    # all bandwidth resources to distribute must be stored as net! leftover value in cpu will also be subtracted from net reward pool
    action_data = {
      "initresource" : {
        "code" : "eosio",
        "action" : "initresource",
        "authorized_by" : "eosio",
        "args" : {
          "receiver" : "beos.distrib",
          "bytes" : -1,
          "stake_net_quantity" : balance_int,
          "stake_cpu_quantity" : config.DISTRIB_NETCPU_LEFTOVER
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "eosio", action_data, "active")
    # eosio.get_account("eosio")
    # eosio.get_account("beos.distrib")

    action_data = {
      "storeparams" : {
        "code" : "beos.init",
        "action" : "storeparams",
        "authorized_by" : "beos.init",
        "args" : {
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "beos.init", action_data, "active")

    action_data = {
      "storeparams" : {
        "code" : "beos.distrib",
        "action" : "storeparams",
        "authorized_by" : "beos.distrib",
        "args" : {
        }
      }
    }
    eosio_rpc_actions.push_action("eosio", "beos.distrib", action_data, "active")

    eosio_tools.wait_for_blocks_produced(10, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    eosio_runner.terminate_running_tasks()
  except Exception as ex:
    eosio_runner.terminate_running_tasks()
    logger.error("Exception during initialize: {0}".format(ex))
    sys.exit(1)