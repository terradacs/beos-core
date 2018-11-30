import re
import json
import time
import queue
import threading 
import requests
import datetime

from logger import log

class EOSRPCExecutor():
    def __init__(self, _nodeos_addres, _nodeos_port, _wallet_address, _wallet_port, _wallet_name):
        self.nodeos_url = 'http://'+_nodeos_addres +":"+_nodeos_port
        self.wallet_url = 'http://'+_wallet_address+":"+_wallet_port
        self.wallet_name = _wallet_name
        self.action_queue = queue.Queue()
        self.action_execution_flag = threading.Event()
        self.action_execution_flag.set()
        self.action_executer_th = threading.Thread(target=self.execute_pending_actions)
        self.action_executer_th.setDaemon(daemonic=True)
        self.action_executer_th.start()
        self.actions_call_summary = []


    def clear_action_flag(self):
        self.action_execution_flag.clear()


    def execute_pending_actions(self):
        while self.action_execution_flag.isSet():
            action = self.action_queue.get()
            if action :
                self.prepare_and_push_transaction(action)
            else :
                break


    def push_action(self, _action):
        self.action_queue.put(_action)


    def extend_expiration_time(self, _time, _extend_by_seconds = 60):
        format = "%Y-%m-%dT%H:%M:%S.%f"
        d = datetime.datetime.strptime(_time, format)
        d = d + datetime.timedelta(seconds = _extend_by_seconds)
        return datetime.datetime(d.year, d.month, d.day, d.hour, d.minute , d.second).strftime(format)


    def get_account(self, _account_name):
        try:
            url = self.nodeos_url+"/v1/chain/get_account"
            command = {"account_name":_account_name}
            response = requests.post(url, json=command)
            log.info("Get account %s"%response.json())
            return response.json()
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during get_account"%str(_ex))        
            

    def create_key(self):
        #curl -X POST --url http://127.0.0.1:8900/v1/wallet/create_key --data '["beos_master_wallet",""]'
        #"EOS5pXMSt54C83tdHkv73c884xRU4TDpDpxDiWJgtDWRDa2N4XfMp"
        try:
            url      = self.wallet_url+"/v1/wallet/create_key"
            data     = "[\"%s\",\"\"]"%(self.wallet_name)
            resspone = requests.post(url, data=data)

            return resspone.text[1:-1]
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during get_account"%str(_ex))


    def get_currency_balance(self, _account_name, _symbol, ):
        try:
            url = self.nodeos_url+'/v1/chain/get_currency_balance'
            command = {"account":_account_name,"symbol":_symbol, "code":"eosio.token"}
            response = requests.post(url, json=command)
            text = response.text
            dig = re.search("\d", text)
            if dig:
                whole = text[text.find("\"")+1:text.rfind("\"")]
            else:
                whole = ""
            response_json ={"balance":whole}
            log.info("Get currency balance %s"%response_json)
            return response_json
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during get_currency_balance"%str(_ex))            


    def get_public_keys(self):
        try:
            url = self.wallet_url+'/v1/wallet/get_public_keys'
            response = requests.post(url)
            text = response.text
            keys = text[text.find("[")+1:text.rfind("]")]
            keys = keys.split(",")
            av = []
            for k in keys:
                temp = k[k.find("\"")+1:k.rfind("\"")]
                av.append(temp)
            return av
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during get_currency_balance"%str(_ex))            


    def create_account_action(self, _newaccount):
        name      = _newaccount["name"]
        owner_key = _newaccount["owner_pub"]
        activ_key = _newaccount["activ_pub"]
        cmd = [{
        "code":"eosio",
        "action":"newaccount",
        "authorized_by":"beos.gateway",
        "args":{
              "creator": "beos.gateway",
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
                    "key": activ_key,
                    "weight": 1
                  }
                ],
                "accounts": [],
                "waits": []
              }
            }
        }
        ]
        return cmd

    def prepare_and_push_transaction(self, _actions):
        try:
            actions =[]
            expected_result = {"status":True}
            if isinstance(_actions, list):
                actions = _actions
            else:
                actions.append(_actions)

            prepared_actions = []
            try:
                for action in actions:
                    if action["action"] == "newaccount_pattern":
                        new_action = self.create_account_action(action)
                        for na in new_action:
                            binargs = self.abi_to_json_bin(na)
                            prepared_actions = self.prepare_action(na, binargs, prepared_actions)
                            if "expected_result" in action:
                                log.info("expected_result %s"%action["expected_result"])
                                expected_result = action.pop("expected_result")
                    else:
                        binargs = self.abi_to_json_bin(action)
                        prepared_actions = self.prepare_action(action, binargs, prepared_actions)
                        if "expected_result" in action:
                            log.info("expected_result %s"%action["expected_result"])
                            expected_result = action.pop("expected_result")
                last_block_id   = self.get_info()
                last_block_info = self.get_block(last_block_id)
                public_keys     = self.get_public_keys()
                log.info("public keys: %s"%public_keys)
                required_key    = self.get_required_keys(prepared_actions, binargs, last_block_info, public_keys)
                log.info("required keys: %s"%required_key)
                signed_transaction = self.sign_transaction(prepared_actions, binargs, last_block_id, last_block_info, required_key)
                transaction_status = self.push_transaction(prepared_actions, binargs, signed_transaction)
                if "transaction_id" in transaction_status:
                    log.info("[ACTION][OK] %s pushed to block %d"%(actions, transaction_status["processed"]["block_num"]))
                    self.actions_call_summary.append([actions, expected_result, True])
                else:
                    log.error("[ACTION][ERROR] failed to push action %s to block"%(actions))
                    self.actions_call_summary.append([actions, expected_result, transaction_status["error"]["details"]])
            except Exception as _ex:
                log.error("[ACTION][ERROR] exception %s occures during prepare_and_push_transaction"%str(_ex))
                log.error("[ACTION][ERROR] failed to push action %s to block"%(actions))
                self.actions_call_summary.append([actions, expected_result, False])
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception %s occures during prepare_and_push_transaction"%str(_ex))
            log.error("[ACTION][ERROR] failed to push action %s to block"%(actions))
            self.actions_call_summary.append([actions, expected_result, False])

 
    def prepare_action(self, _action, _binargs, _prepared_actions):
        _prepared_actions.append( { "account": _action["code"],
                "name":  _action["action"],
                "authorization": [ { "actor":_action.pop("authorized_by"),
                                    "permission":"active"}],
                "data":_binargs["binargs"]})
        return _prepared_actions

 
    def abi_to_json_bin(self, _action):
        try:
            response = requests.post(self.nodeos_url+'/v1/chain/abi_json_to_bin', json = _action)
            response_json = response.json()
            needed_data = { "binargs": response_json["binargs"]}
            return needed_data
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during abi_to_json_bin"%str(_ex))

 
    def get_info(self):
        try:
            response = requests.get(self.nodeos_url+'/v1/chain/get_info')
            response_json = response.json()
            return response_json
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during get_info"%str(_ex))


 
    def get_block(self, _block_num_or_id):
        try:
            data = {"block_num_or_id":_block_num_or_id["head_block_num"]}
            response = requests.post(self.nodeos_url+'/v1/chain/get_block', json = data)
            response_json = response.json()
            needed_data = { "timestamp":response_json["timestamp"], "block_num":response_json["block_num"], "ref_block_prefix":response_json["ref_block_prefix"] }
            return needed_data
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during get_block"%str(_ex))            

 
    def get_required_keys(self, _action, _binargs, _last_block_info, _keys):
        try:
            data = {
                "available_keys":_keys,
                "transaction":{
                "actions":_action, 
                    "context_free_actions": [],
                    "context_free_data": [],
                    "delay_sec": 0,
                    "expiration": self.extend_expiration_time(_last_block_info["timestamp"]),
                    "max_kcpu_usage": 0,
                    "max_net_usage_words": 0,
                    "ref_block_num": _last_block_info["block_num"],
                    "ref_block_prefix": _last_block_info["ref_block_prefix"],
                    "signatures": []
                }
            }
            response = requests.post(self.nodeos_url+'/v1/chain/get_required_keys', json=data)
            response_json = response.json()
            needed_data = { "required_keys":response_json["required_keys"] }
            return needed_data
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during get_required_keys"%str(_ex))

 
    def sign_transaction(self, _action, _binargs, _last_block_id, _last_block_info, _required_key):
        try:
            data = [{
                    "ref_block_num":_last_block_info["block_num"],
                    "ref_block_prefix":_last_block_info["ref_block_prefix"],
                    "expiration" : self.extend_expiration_time(_last_block_info["timestamp"]),
                    "actions" : _action,  
                    "signatures":[],
                    },
                    _required_key["required_keys"]
                    ,_last_block_id["chain_id"]]
            response = requests.post(self.wallet_url+'/v1/wallet/sign_transaction', json=data)
            return response.json()
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during sign_transaction"%str(_ex))

 
    def push_transaction(self, _action, _binargs, _signed_transaction):
        try:
            data = {
                "compression": "none",
                "transaction": {
                    "expiration": _signed_transaction["expiration"],
                    "ref_block_num": _signed_transaction["ref_block_num"],
                    "ref_block_prefix": _signed_transaction["ref_block_prefix"],
                    "context_free_actions": [],
                    "actions" : _action,
                    "transaction_extensions": []
                },
                "signatures": _signed_transaction["signatures"]
            }
            response = requests.post(self.nodeos_url+'/v1/chain/push_transaction', data=json.dumps(data))
            return response.json()
        except Exception as _ex:
            log.error("[ACTION][ERROR] exception  %s occures during push_transaction"%str(_ex))


    def get_actions_call_summary(self):
        return self.actions_call_summary


    def clear_actions_call_summary(self):
        self.actions_call_summary = []
