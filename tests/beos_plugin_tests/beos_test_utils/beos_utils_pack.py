import os
import sys
import json
import socket	
import requests
import threading

from time import sleep

from beos_test_utils.logger        import add_handler, log
from beos_test_utils.beosnode      import BEOSNode
from beos_test_utils.summarizer    import *
from beos_test_utils.cmdlineparser import parser
from beos_test_utils.cluster       import Cluster


class BEOSUtilsException(Exception):
    def __init__(self, _message):
        self.message = _message

    def __str__(self):
        return "BEOSUtilsException exception `{0}`".format(self.message)

def init(_file, _bios = False):
    try:
        data = os.path.split(_file)
        cdir = data[0] if data[0] else "."
        cfile = data[1]
        args = parser.parse_args()
        node = BEOSNode(args.nodeos_ip, args.nodeos_port, args.keosd_ip,
            args.keosd_port, args.master_wallet_name, args.path_to_cleos)
        node.set_node_dirs(cdir+"/node/"+cfile, cdir+"/logs/"+cfile, _new_dir = _bios)
        summary = Summarizer(cdir+"/"+cfile)
        add_handler(cdir+"/logs/"+ cfile+"/"+cfile)

        return node, summary, args, log
    except Exception as _ex:
        raise BEOSUtilsException(str(_ex))

def init_cluster(_file, _pnodes, _producers_per_node):
    bios_node, summary, args, log = init(_file, True)
    log_handlers = log.handlers
    cluster = Cluster(bios_node, _pnodes, _producers_per_node, _file)
    cluster.initialize_bios()
    log.handlers = log_handlers
    return cluster, summary, args, log


def get_transaction_id_from_result(code, result):
  """ Get transaction id from different types of transactions """
  if result.find("Transaction will be deferred due to the jurisdictions") != -1:
    data = json.loads(result)
    return data["trx_id"]
  elif result.find("executed transaction:" ) != -1: 
      tmp = result.split()
      for idx, item in enumerate(tmp):
          if item == "transaction:":
              trx_id = tmp[idx+1]
              return trx_id
  else:
    return None

class JurisdictionCodeChanger(threading.Thread):
  def __init__(self,api_node_url,producer_node_url,codes):
      threading.Thread.__init__(self)
      self.shutdown_requested = False
      self.codes = codes
      self.api_node_url = api_node_url
      self.producer_node_url = producer_node_url
      self.reporting_interval = 60
      self.current_index = 0

  def get_current_jurisdiction_map(self, api_node_url):
    get_all_jurisdictions_url = api_node_url + "/v1/jurisdiction/get_all_jurisdictions"
    headers = {'content-type': 'application/json; charset=UTF-8'}
    response = requests.request("POST", get_all_jurisdictions_url, headers=headers)
    get_all_jurisdictions = response.json()
    name_code = {}
    code_name = {}
  
    for jurisdiction in get_all_jurisdictions["jurisdictions"]:
        name_code[jurisdiction["name"]] = int(jurisdiction["code"])
        code_name[int(jurisdiction["code"])] = jurisdiction["name"]
    return name_code, code_name

  def set_jurisdiction_for_producer(self, producer_node_url, jurisdiction_code):
    set_jurisdiction_for_producer_url = producer_node_url + "/v1/gps/update_jurisdictions"
    headers = {'content-type': 'application/json; charset=UTF-8'}
    payload = {"jurisdictions" : jurisdiction_code}
  
    requests.post(set_jurisdiction_for_producer_url, data=json.dumps(payload), headers=headers)

  def run(self):
    name_code, code_name = self.get_current_jurisdiction_map(self.api_node_url)
    while not self.shutdown_requested:
      current_code = self.codes[self.current_index]
      jurisdiction_name = code_name.get(current_code, None)
      if jurisdiction_name is not None:
        self.set_jurisdiction_for_producer(self.producer_node_url, [current_code])
      self.current_index += 1
      if self.current_index >= len(self.codes):
        self.current_index = 0
      sleep(self.reporting_interval)

  def stop(self):
      self.shutdown_requested = True

  def is_running(self):
      return not self.shutdown_requested