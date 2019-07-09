#!/usr/bin/python3

"""
This script will assist with upgrade of regular BEOS node to jurisdiction aware one.
"""

import logging
import sys

MODULE_NAME = "BEOS upgrade"
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
MAIN_LOG_PATH = './upgrade.log'

UPGRADE_DATA_DIR = "./upgrade-data/"

logger = logging.getLogger(MODULE_NAME)
logger.setLevel(LOG_LEVEL)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(LOG_LEVEL)
ch.setFormatter(logging.Formatter(LOG_FORMAT))

fh = logging.FileHandler(MAIN_LOG_PATH)
fh.setLevel(LOG_LEVEL)
fh.setFormatter(logging.Formatter(LOG_FORMAT))

logger.addHandler(ch)
logger.addHandler(fh)

from common import run_command_and_return_output

def save_contract_data(cleos_bin, node_url, wallet_url, contract_name):
  logger.info("Saving original {} contract data".format(contract_name))
  abi_path = "{}{}.orig.abi".format(UPGRADE_DATA_DIR, contract_name)
  wast_path = "{}{}.orig.wast".format(UPGRADE_DATA_DIR, contract_name)
  parameters = [
    cleos_bin,
    "--url", node_url,
    "--wallet-url", wallet_url,
    "get", "code",
    "-c", wast_path,
    "-a", abi_path,
    contract_name
  ]
  retcode, out = run_command_and_return_output(parameters)
  contract_hash = None
  if retcode == 0:
    out = out.decode("utf-8")
    logger.info("Contract {} saved to: {} and {}".format(contract_name, abi_path, wast_path))
    contract_hash = out.split("\n")[0].split(" ")[-1]
    logger.info("Contract data hash: {}".format(contract_hash))
    return (contract_hash, abi_path, wast_path)
  raise RuntimeError("Failed to save contract data {}".format(contract_name))

def prepare_contract_data(cleos_bin, node_url, wallet_url, contract_dir, contract_name):
  logger.info("Preparing new contract data for {}".format(contract_name))
  parameters = [
    cleos_bin,
    "--url", node_url,
    "--wallet-url", wallet_url,
    "set", "contract",
    "-s", "-j", "-d",
    contract_name,
    contract_dir,
    "--suppress-duplicate-check"
  ]
  retcode, out = run_command_and_return_output(parameters)
  if retcode == 0:
    out = out.decode("utf-8")
    with open("{}upgrade_{}.json".format(UPGRADE_DATA_DIR, contract_name), "w") as f:
      f.writelines(out)
    logger.info("Done")
    return
  raise RuntimeError("Failed to prepare contract data for {}".format(contract_name))

def compare_transaction_data(my_copy_path, outside_copy_path, diff_file_path):
  logger.info("Attempting to compare transaction data between local data {} and sent data {}".format(my_copy_path, outside_copy_path))
  with open(my_copy_path, "r") as my_copy:
    with open(outside_copy_path, "r") as outside_copy:
      difference = set(my_copy).difference(outside_copy)
      difference.discard('\n')

      with open(diff_file_path, 'w') as diff_file:
        logger.info("Writting diff file to {}".format(diff_file_path))
        for line in difference:
          diff_file.write(line)

      return difference
  return None

def get_chain_id(cleos_bin):
  parameters = [
    cleos_bin,
    "get", "info"
  ]
  retcode, out = run_command_and_return_output(parameters)
  if retcode == 0:
    import json
    data = json.loads(out.decode("utf-8"))
    return data.get("chain_id", None)
  return None

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('node_url', type=str, help="URL of producer node for contract upgrade")
  parser.add_argument('wallet_url', type=str, help="URL for keosd service")
  parser.add_argument('cleos_bin', type=str, help="Path to cleos executable")
  parser.add_argument('contract_dir', type=str, help="Directory with upgraded contracts")
  parser.add_argument('old_contract_name', type=str, help="Name of the contract to backup")
  parser.add_argument('upgraded_contract_name', type=str, help="Name of the contract to upgrade")
  parser.add_argument('--compare-with', dest="compare_with", type=str, help="Compare official transaction data with local transaction data")

  args = parser.parse_args()

  try:
    from os.path import exists
    chain_id = get_chain_id(args.cleos_bin)
    if chain_id is None:
      raise RuntimeError("Error querying chain id")
    logger.info("Chain id: {}".format(chain_id))
    if not exists(UPGRADE_DATA_DIR):
      logger.info("{} does not exists. Creating...".format(UPGRADE_DATA_DIR))
      from os import makedirs
      makedirs(UPGRADE_DATA_DIR)

    save_contract_data(args.cleos_bin, args.node_url, args.wallet_url, args.old_contract_name)
    prepare_contract_data(args.cleos_bin, args.node_url, args.wallet_url, args.contract_dir, args.old_contract_name)
    if args.compare_with:
      my_copy_path = "{}upgrade_{}.json".format(UPGRADE_DATA_DIR, args.upgraded_contract_name)
      diff_file_path = '{}contract_diff.txt'.format(UPGRADE_DATA_DIR)
      file_diff = list(compare_transaction_data(my_copy_path, args.compare_with, diff_file_path))

      file_diff_len = len(file_diff)
      if file_diff_len != 3:
        raise RuntimeError("Something is wrong with diff file. There should be three different lines: in expiration, ref_block_num, ref_block_prefix.")

  except Exception as ex:
    logger.error("Error during upgrade {}".format(ex))