#!/usr/bin/python3

import logging
import sys

MODULE_NAME = "BEOS add jurisdictions"
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
MAIN_LOG_PATH = './add_jurisdictions.log'

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

def add_jurisdictions(cleos_bin, node_url, wallet_url, jurisdiction_data):
  from time import sleep
  for jurisdiction in jurisdiction_data["default"]:
    logger.info("Adding new jurisdiction code {} with name {}".format(jurisdiction["code"], jurisdiction["name"]))
    parameters = [
      cleos_bin,
      "--url", node_url,
      "--wallet-url", wallet_url,
      "push", "action", "eosio", "addjurisdict",
      '[ "eosio", "{}", "{}", "{}" ]'.format(jurisdiction["code"], jurisdiction["name"], jurisdiction["description"]), 
      '-p', "eosio"
    ]
    retcode, out = run_command_and_return_output(parameters)
    if retcode == 0:
      logger.info("Success")
    else:
      out = out.decode("utf-8")
      if "jurisdiction with the same code exists" in out:
        logger.warning("Failed - jurisdiction exists")
      else:
        logger.error("Failed - {}".format(out))
    sleep(1./200)

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('node_url', type=str, help="URL of producer node for contract upgrade")
  parser.add_argument('wallet_url', type=str, help="URL for keosd service")
  parser.add_argument('cleos_bin', type=str, help="Path to cleos executable")
  parser.add_argument('jurisdiction_src', type=str, help="Path to json file with jurisdiction definitions")
  args = parser.parse_args()

  try:
    with open(args.jurisdiction_src) as f:
      import json
      jurisdiction_data = json.loads(f.read())
      add_jurisdictions(args.cleos_bin, args.node_url, args.wallet_url, jurisdiction_data)
  except Exception as ex:
    logger.error("Error during upgrade {}".format(ex))