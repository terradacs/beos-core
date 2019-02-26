import json


class ActionException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return "BEOS action exception: `{0}`".format(self.message)


class ActionBase(object):
    def __init__(self):
        self.action = None


    def make_action(self):
        if self.action:
            return self.action
        else:
            raise ActionException("Action not implemented.")


class BuyRamAction(ActionBase):
    def __init__(self, _payer, _receiver, _quant, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio" ,
            "authorized_by": _authorized_by if _authorized_by else _payer,
            "action": "buyram",
            "args": {
                "payer": _payer,
                "receiver": _receiver,
                "quant": _quant
            }
        }


class BuyRamBytesAction(ActionBase):
    def __init__(self, _payer, _receiver, _bytes, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio" ,
            "authorized_by": _authorized_by if _authorized_by else _payer,
            "action": "buyrambytes",
            "args": {
                "payer": _payer,
                "receiver": _receiver,
                "bytes": _bytes
            }
        }


class ChangeparamsInitAction(ActionBase):
    def __init__(self, _start_election, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "beos.init",
            "action":"changeparams",
            "authorized_by": _authorized_by if _authorized_by else "beos.init",
            "args":{
                "new_params":{ "starting_block_for_initial_witness_election":_start_election["starting_block_for_initial_witness_election"] }
            }
        }


class ChangeparamsDistributionAction(ActionBase): 
    def __init__(self, _asset , _beos_data, _ram_data, _ram_leftover, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "beos.distrib",
            "action":"changeparams",
            "authorized_by": _authorized_by if _authorized_by else "beos.distrib",
            "args":{
                "new_params": {
                    "beos":_beos_data["beos"],
                    "ram":_ram_data["ram"],
                    "proxy_assets":_asset["proxy_assets"], 
                    "ram_leftover":_ram_leftover["ram_leftover"]
                }
            }
        }


class CreateAccountAction(ActionBase):
    def __init__(self, _creator, _name, _owner_key, _active_key, _init_ram = True, _authorized_by = None, _code = None)  :     
        self.action = {
            "code": _code if _code else "eosio",
            "action":"newaccount",
            "authorized_by": _authorized_by if _authorized_by else _creator,
            "args":{
                    "creator": _creator,
                    "name": _name,
                    "init_ram": _init_ram,
                    "owner": {
                        "threshold": 1,
                        "keys": [{
                            "key": _owner_key,
                            "weight": 1
                            }
                        ],
                        "accounts": [],
                        "waits": []
                    },
                    "active": {
                        "threshold": 1,
                        "keys": [{
                            "key": _active_key,
                            "weight": 1
                            }
                        ],
                        "accounts": [],
                        "waits": []
                    }
                }
        }


class DelegatebwAction(ActionBase):
    def __init__(self, _from, _receiver, _stake_net_quantity, _stake_cpu_quantity, _transfer = False, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio",
            "action": "delegatebw",
            "authorized_by": _authorized_by if _authorized_by else _from,
            "args": {
                "from": _from,
                "receiver": _receiver,
                "stake_net_quantity": _stake_net_quantity,
                "stake_cpu_quantity": _stake_cpu_quantity,
                "transfer": _transfer
            }
        }


class IssueAction(ActionBase):
    def __init__(self, _from, _to, _quantity, _memo, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "beos.gateway",
            "action": "issue",
            "authorized_by": _authorized_by if _authorized_by else _from,
            "args": {
                "from": _from,
                "to": _to,
                "quantity": _quantity, 
                "memo": _memo
            }
        }


class RegproducerAction(ActionBase):
    def __init__(self, _producer, _producer_key, _url, _location, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio",
            "action": "regproducer",
            "authorized_by": _authorized_by if _authorized_by else _producer,
            "args": {
                    "producer": _producer,
                    "producer_key": _producer_key,
                    "url": _url,
                    "location": _location
            }
        }

class UnregprodAction(ActionBase):
    def __init__(self, _producer, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio",
            "action": "unregprod",
            "authorized_by": _authorized_by if _authorized_by else _producer,
            "args": {
                    "producer": _producer
            }
        }

class SellramAction(ActionBase):
    def __init__(self, _account, _bytes, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio",
            "action": "sellram",
            "authorized_by": _authorized_by if _authorized_by else _account,
            "args": {
                "account": _account,
                "bytes": _bytes
            }
        }


class TransferAction(ActionBase):
    def __init__(self, _from, _to, _quantity, _memo, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio.token",
            "action": "transfer",
            "authorized_by": _authorized_by if _authorized_by else _from,
            "args": {
                "from": _from,
                "to": _to,
                "quantity": _quantity, 
                "memo": _memo
            }
        }


class UndelegatebwAction(ActionBase):
    def __init__(self, _from, _receiver, _unstake_net_quantity, _unstake_cpu_quantity, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio",
            "action": "undelegatebw",
            "authorized_by": _authorized_by if _authorized_by else _from,
            "args": {
                "from": _from,
                "receiver": _receiver,
                "unstake_net_quantity": _unstake_net_quantity,
                "unstake_cpu_quantity": _unstake_cpu_quantity
            }
        }


class VoteproducerAction(ActionBase):
    def __init__(self, _voter, _proxy, _producers, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "eosio",
            "action": "voteproducer",
            "authorized_by": _authorized_by if _authorized_by else _voter,
            "args": {
                "voter": _voter,
                "proxy": _proxy,
                "producers": _producers if isinstance(_producers, list) else [_producers]
            }
        }


class WithdrawAction(ActionBase):
    def __init__(self, _from, _bts_to, _quantity, _memo, _authorized_by = None, _code = None):
        self.action = {
            "code": _code if _code else "beos.gateway",
            "action": "withdraw",
            "authorized_by": _authorized_by if _authorized_by else _from,
            "args": {
                "from": _from,
                "bts_to": _bts_to,
                "quantity": _quantity,
                "memo": _memo
            }
        }
