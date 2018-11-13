import json
import time
import queue
import threading 
import requests
import datetime

class EOSRPCExecutor():
    def __init__(self, _nodeos_addres, _nodeos_port, _wallet_address, _wallet_port):
        self.nodeos_url = 'http://'+_nodeos_addres +":"+_nodeos_port
        self.wallet_url = 'http://'+_wallet_address+":"+_wallet_port
        self.action_queue = queue.Queue()
        self.action_execution_flag = threading.Event()
        self.action_execution_flag.set()
        self.action_executer_th = threading.Thread(target=self.execute_pending_actions)
        self.action_executer_th.setDaemon(daemonic=True)
        self.action_executer_th.start()


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
            return response.json()
        except Exception as _ex:
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception  %s occures during get_account"%str(_ex))        
            

    def get_currency_balance(self, _account_name, _symbol, ):
        try:
            url = self.nodeos_url+'/v1/chain/get_currency_balance'
            command = {"account":_account_name,"symbol":_symbol, "code":"eosio.token"}
            response = requests.post(url, json=command)
            text = response.text
            whole = text[text.find("\"")+1:text.rfind("\"")]
            response_json ={"balance":whole}
            return response_json
        except Exception as _ex:
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception  %s occures during get_currency_balance"%str(_ex))            


    def prepare_and_push_transaction(self, _actions):
        try:
            actions =[]
            if isinstance(_actions, list):
                actions = _actions
            else:
                actions.append(_actions)

            prepared_actions = []
            for action in actions:
                binargs = self.abi_to_json_bin(action)
                prepared_actions = self.prepare_action(action, binargs, prepared_actions)
            last_block_id = self.get_info()
            last_block_info = self.get_block(last_block_id)
            required_key    = self.get_required_keys(prepared_actions, binargs, last_block_info)
            signed_trasnaction = self.sign_transaction(prepared_actions, binargs, last_block_id, last_block_info, required_key)
            transaction_status = self.push_transaction(prepared_actions, binargs, signed_trasnaction)
            if "transaction_id" in transaction_status:
                print(str(datetime.datetime.now())[:-3], "[ACTION][OK] %s pushed to block %d"%(actions, transaction_status["processed"]["block_num"]))
            else:
                print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] failed to push action %s to block"%(actions))
        except Exception as _ex:
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception %s occures during prepare_and_push_transaction"%str(_ex))
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] failed to push action %s to block"%(actions))

 
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
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception  %s occures during abi_to_json_bin"%str(_ex))

 
    def get_info(self):
        try:
            response = requests.get(self.nodeos_url+'/v1/chain/get_info')
            response_json = response.json()
            return response_json
        except Exception as _ex:
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception  %s occures during get_info"%str(_ex))


 
    def get_block(self, _block_num_or_id):
        try:
            data = {"block_num_or_id":_block_num_or_id["head_block_num"]}
            response = requests.post(self.nodeos_url+'/v1/chain/get_block', json = data)
            response_json = response.json()
            needed_data = { "timestamp":response_json["timestamp"], "block_num":response_json["block_num"], "ref_block_prefix":response_json["ref_block_prefix"] }
            return needed_data
        except Exception as _ex:
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception  %s occures during get_block"%str(_ex))            

 
    def get_required_keys(self, _action, _binargs, _last_block_info):
        try:
            data = {
                "available_keys":["EOS53QRGWCMxxHtKqFjiMQo8isf3so1dUSMhPezceFBknF8T5ht9b",
                                "EOS6AAWx6uvqu5LMBt8vCNYXcxjrGmd3WvffxkBM4Uozs4e1dgBF3",
                                "EOS8imf2TDq6FKtLZ8mvXPWcd6EF2rQwo8zKdLNzsbU9EiMSt9Lwz",
                                "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV",
                                "EOS6Y1LJCZC1Mrp9EoLcmkobJHoNnVQMqLcNAxU5xL5iXwqzctjmd",
                                "EOS5FUjQDE6QLiGZKt7hGwBypCAJPL53X3SYf6Gf4JxMkdyH1wMrF"],
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
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception  %s occures during get_required_keys"%str(_ex))

 
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
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception  %s occures during sign_transaction"%str(_ex))

 
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
                "signatures": [
                        _signed_transaction["signatures"][0]
                ]
                }
            response = requests.post(self.nodeos_url+'/v1/chain/push_transaction', data=json.dumps(data))
            return response.json()
        except Exception as _ex:
            print(str(datetime.datetime.now())[:-3], "[ACTION][ERROR] exception  %s occures during push_transaction"%str(_ex))