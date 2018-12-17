#!/usr/bin/env python3

import config
import eosio_tools
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

    wallet_url = "http://{0}:{1}".format(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT)
    eosio_runner.run_keosd(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT, config.DEFAULT_WALLET_DIR, False, True)
    eosio_rpc_actions.create_wallet()
    eosio_runner.run_nodeos(config.START_NODE_INDEX, config.PRODUCER_NAME, config.EOSIO_PUBLIC_KEY)

    eosio_rpc_actions.create_account("eosio", "eosio.msig", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY, True)

    eosio_tools.wait_for_blocks_produced(10, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
    eosio_runner.terminate_running_tasks()
  except Exception as ex:
    eosio_runner.terminate_running_tasks()
    logger.error("Exception during initialize: {0}".format(ex))
    sys.exit(1)