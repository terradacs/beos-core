import re
import json
import requests
import datetime

from beos_test_utils.logger        import log
from beos_test_utils.summarizer    import *
from beos_test_utils.eoscallerbase import EOSCallerBase


class EOSTransactionCaller(EOSCallerBase):
    def __init__(self, _node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name):
        super(EOSTransactionCaller, self).__init__(_node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name)


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
            log.exception("Exception `%s` occures during get_account"%str(_ex))        


    def import_private_key(self, _private_key):
        try:
            #Private key: 5K4Mrs5DWTQnkSJRJr8SpBcWUgm9LmQcndaQdPzqay8QYywHYHp
            #Public key: EOS4xzVw3UxezBGgDrEy87amhuSBSo41A3vW7JNRRv6wMd9EQPCRJ
            url      = self.keosd_url+"/v1/wallet/import_key"
            data     = "[\"%s\",\"%s\"]"%(self.wallet_name, _private_key)
            resspone = requests.post(url, data=data)
            return resspone.text[1:-1]
        except Exception as _ex:
            log.exception("Exception `%s` occures during get_account"%str(_ex))


    def create_key(self):
        try:
            url      = self.keosd_url+"/v1/wallet/create_key"
            data     = "[\"%s\",\"\"]"%(self.wallet_name)
            resspone = requests.post(url, data=data)
            return resspone.text[1:-1]
        except Exception as _ex:
            log.exception("Exception `%s` occures during get_account"%str(_ex))


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
            log.exception("Exception `%s` occures during get_currency_balance"%str(_ex))            


    def get_public_keys(self):
        try:
            url = self.keosd_url+'/v1/wallet/get_public_keys'
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
            log.exception("Exception `%s` occures during get_currency_balance"%str(_ex))            


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
            log.exception("Exception `%s` occures during abi_to_json_bin"%str(_ex))

 
    def get_info(self):
        try:
            response = requests.get(self.nodeos_url+'/v1/chain/get_info')
            response_json = response.json()
            return response_json
        except Exception as _ex:
            log.exception("Exception `%s` occures during get_info"%str(_ex))


 
    def get_block(self, _block_num_or_id):
        try:
            data = {"block_num_or_id":_block_num_or_id["head_block_num"]}
            response = requests.post(self.nodeos_url+'/v1/chain/get_block', json = data)
            response_json = response.json()
            needed_data = { "timestamp":response_json["timestamp"], "block_num":response_json["block_num"], "ref_block_prefix":response_json["ref_block_prefix"] }
            return needed_data
        except Exception as _ex:
            log.exception("Exception `%s` occures during get_block"%str(_ex))            

 
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
            log.exception("Exception `%s` occures during get_required_keys"%str(_ex))

 
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
            response = requests.post(self.keosd_url+'/v1/wallet/sign_transaction', json=data)
            return response.json()
        except Exception as _ex:
            log.exception("Exception `%s` occures during sign_transaction"%str(_ex))

 
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
            log.exception("Exception `%s` occures during push_transaction"%str(_ex))


    def prepare_and_push_transaction(self, _actions):
        try:
            actions =[]
            if isinstance(_actions, list):
                actions = _actions
            else:
                actions.append(_actions)

            prepared_actions = []
            try:
                for action in actions:
                    binargs = self.abi_to_json_bin(action)
                    prepared_actions = self.prepare_action(action, binargs, prepared_actions)
                last_block_id   = self.get_info()
                last_block_info = self.get_block(last_block_id)
                public_keys     = self.get_public_keys()
                required_key    = self.get_required_keys(prepared_actions, binargs, last_block_info, public_keys)
                log.info("required keys: `%s`"%required_key)
                signed_transaction = self.sign_transaction(prepared_actions, binargs, last_block_id, last_block_info, required_key)
                transaction_status = self.push_transaction(prepared_actions, binargs, signed_transaction)
                if "transaction_id" in transaction_status:
                    log.info("[ACTION][OK] `%s` pushed to block `%d`"%(actions, transaction_status["processed"]["block_num"]))
                    return ActionResult(True, "", transaction_status, actions)
                else:
                    log.error("[ACTION][ERROR] failed to push action `%s` to block"%(actions))
                    return ActionResult(False, transaction_status["error"]["details"], transaction_status, actions)
            except Exception as _ex:
                log.exception("Exception `%s` occures during prepare_and_push_transaction"%str(_ex))
                log.error("[ACTION][ERROR] failed to push action `%s` to block"%(actions))
                return ActionResult(False, "", "", actions)
        except Exception as _ex:
            log.exception("Exception `%s` occures during prepare_and_push_transaction"%str(_ex))
            log.error("[ACTION][ERROR] failed to push action `%s` to block"%(actions))
            return ActionResult(False, "", "", actions)