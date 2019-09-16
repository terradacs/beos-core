import json
import requests
import threading
from time import sleep

def get_transaction_id_from_result(code, result):
  data = json.loads(result)
  return data["trx_id"]

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