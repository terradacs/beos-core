import requests
import json

NODEOS_API_LIST = [
  "chain",
  "history",
  "producer",
  "net"
]

KEOSD_API_LIST = [
  "wallet"
]

class EosioInterface(object):
  def __init__(self, nodeos_ip, nodeos_port, keosd_ip, keosd_port, use_https = False):
    prefix = "http://"
    if use_https:
      prefix = "https://"
    self.nodeos_url = prefix + "{0}:{1}/v1/".format(nodeos_ip, nodeos_port)
    self.keosd_url = prefix + "{0}:{1}/v1/".format(keosd_ip, keosd_port)
    self.nodeos_ip = nodeos_ip
    self.nodeos_port = nodeos_port
    self.keosd_ip = keosd_ip
    self.keosd_port = keosd_port
    self.use_https = use_https
  
  def request(self, api, method, method_args = None):
    print("API: {0}, Method: {1}, Args: {2}".format(api, method, method_args))
    url = None
    if api in NODEOS_API_LIST:
      url = self.nodeos_url
    if api in KEOSD_API_LIST:
      url = self.keosd_url

    url = url + api + "/" + method
    print("Composed url: {0}".format(url))

    try:
      response = requests.request("POST", url, json = method_args)
      return response.json()
    except Exception as ex:
      print("Exception during processing request: {0}".format(ex))
      return None

  def __getattr__(self, name):
    if name in NODEOS_API_LIST or name in KEOSD_API_LIST:
      return EosioInterface.Api(api_name = name, backend = self)
    raise AttributeError("Unknown attribute {!r}".format(name))

  class Api(object):
    def __init__(self, api_name = "", backend = None):
      self.api_name = api_name
      self.backend = backend

    def __getattr__(self, name):
      return EosioInterface.Method(api_name = self.api_name, method_name = name, backend = self.backend)

  class Method(object):
    def __init__(self, api_name = "", method_name = "", backend = None):
      self.api_name = api_name
      self.method_name = method_name
      self.backend = backend

    def __call__(self, args = None):
      return self.backend.request(api = self.api_name, method = self.method_name, method_args = args)
