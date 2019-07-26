
import os
import sys
import time
import random
import string
import datetime
import collections

try:
    from beos_test_utils import run
except Exception as _ex:
    print("Faild to import run.py script. Please make sure that run ./deploy.py --build-beos. Aborting.")
    exit(1)

import beos_test_utils.beosactionpatterns as patterns

from beos_test_utils.logger               import log
from beos_test_utils.eoscleoscaller       import EOSCleosCaller
from beos_test_utils.eostransactioncaller import EOSTransactionCaller
from beos_test_utils.summarizer           import ActionResult

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cd_scripts import eosio_rpc_actions
from cd_scripts import eosio_rpc_client

# we will wait max 240 blocks of time
MAX_WAIT_INTERVALS = 240

class BEOSNode(object):
    node = "node"

    class BEOSNodeData(object):
        def __init__(self, _node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name):
            self.node_ip     = _node_ip 
            self.node_port   = _node_port
            self.keosd_ip    = _keosd_ip
            self.keosd_port  = _keosd_port
            self.wallet_name = _wallet_name,

    def __init__(self, _node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name, _path_to_cleos ):
        self.cleos     = EOSCleosCaller(_node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name, _path_to_cleos)
        self.utils     = EOSTransactionCaller(_node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name)
        self.node_data = BEOSNode.BEOSNodeData(_node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name)
        eosio_rpc_actions.EOSIO = eosio_rpc_client.EosioInterface(self.node_data.node_ip, self.node_data.node_port, self.node_data.keosd_ip, self.node_data.keosd_port)
        eosio_rpc_actions.logger.handlers=[]
        eosio_rpc_actions.logger = log

        self.url = eosio_rpc_client.EosioInterface(self.node_data.node_ip, self.node_data.node_port, self.node_data.keosd_ip, self.node_data.keosd_port)

        self.node_is_running = False
        self.node_number = int(self.node_data.node_port)
        self.node_name   = "{0}-{1}".format(BEOSNode.node, self.node_number)
        self.log_path    = None
        self.working_dir = None
        self.node_producers = {}
        self.delay_block = 0
        self.user_name = list("aaaaaaaaaaaa")


    def generate_user_name(self):
        name = list(self.user_name)
        self.user_name[0] = chr(ord(self.user_name[0]) + 1)
        for i, _ in enumerate(self.user_name):
            if ord(self.user_name[i]) > ord('z'):
                self.user_name[i] = 'a'
                self.user_name[i+1] = chr(ord(self.user_name[i+1]) + 1)
        return ''.join(name)


    def create_accounts(self, _nr_of_accounts, _init_value = None):
        tester = collections.namedtuple("Tester", ('name','akey','okey','init_value'))
        accounts = []
        init_value = _init_value 
        if init_value :
            value = init_value 
        else:
            value = None

        if self.node_is_running:
            stop_node = False
        else:
            self.run_node()
            stop_node = True

        for _ in range(_nr_of_accounts):
            akey = self.utils.create_key()
            okey = self.utils.create_key()
            name = self.generate_user_name()
            self.create_account(name,_activ_key=akey, _owner_key=okey)
            if value:
                self.issue(_from="beos.gateway", _to=name, _quantity=value, _memo="init_value")
            accounts.append(tester(name, akey, okey, value))
        if stop_node:
            self.stop_node()
        return accounts


    def create_producers(self, _nr_of_producers, _init_value = None):
        producers = self.create_accounts(_nr_of_producers, _init_value)
        for producer in producers:
            self.add_producer_to_config(producer.name, producer.akey)
        if self.node_is_running:
            #we need to rerun node to set producers
            self.stop_node()
            self.run_node()
        return producers


    def add_producer_to_config(self, _producer, _key):
        try:
            self.node_producers[_producer]=_key
        except Exception as _ex:
            log.exception("Exception `{0}` occures during adding producers`{1}`".format(str(_ex), self.node_name))
        

    def set_node_dirs(self, _workdir, _log_path, _prod = None, _new_dir = False):
        try:
            self.log_path    = _log_path
            self.working_dir = _workdir 
            if not os.path.exists(self.working_dir):
                os.makedirs(self.working_dir)
            if not os.path.exists(self.log_path):
                os.makedirs(self.log_path)
            run.clone_nodeos(self.working_dir, self.node_number, self.node_name,  None, True, None, _new_dir, False)
        except Exception as _ex:
            log.exception("Exception `{0}` occures during setting node dirs `{1}`".format(str(_ex), self.node_name))


    def run_node(self, _synth_with = None, _remove_eosio_as_producer = False, _genesis_json = None, _just_run = False):
        try:
            if _just_run:
                run.run_custom_nodeos(self.node_number, self.node_name, self.working_dir, self.log_path, True, _genesis_json)
            else:
                run.clone_nodeos(self.working_dir, self.node_number, self.node_name,  self.node_producers, False, _synth_with, False, _remove_eosio_as_producer)
                run.run_custom_nodeos(self.node_number, self.node_name, self.working_dir, self.log_path, None, _genesis_json)
            
            self.node_is_running = True
            self.start_block_nr = self.utils.get_info()["head_block_num"]
            return self.start_block_nr
        except Exception as _ex:
            log.exception("Exception `{0}` occures during initialization of node `{1}`".format(str(_ex), self.node_name))


    def stop_node(self):
        try:
            if self.node_is_running:
                run.kill_process(self.working_dir+"/run_nodeos_{0}_{1}.pid".format(self.node_number, self.node_name,), "nodeos", self.node_data.node_ip, self.node_data.node_port)
                self.node_is_running = False
        except Exception as _ex:
            log.exception("Exception `{0}` occures during stoping node `{1}`".format(str(_ex), self.node_name))

    #def changeparams(self, _asset,  _election_block, _beos_params, _ram_params, _ram_leftover):
    def changeparams(self, _newparams):
        try:
            election_block = {"starting_block_for_initial_witness_election":_newparams["starting_block_for_initial_witness_election"]+ self.start_block_nr}
            changeparams_init   = patterns.ChangeparamsInitAction( election_block )
            self.make_action_call(changeparams_init.make_action())
            
            asset        = {"proxy_assets":_newparams["proxy_assets"]}
            ram_leftover = {"ram_leftover":_newparams["ram_leftover"]}
            beos_params = {"beos":{ "starting_block": _newparams["beos"]["starting_block"] + self.start_block_nr,
                             "next_block": _newparams["beos"]["next_block"], 
                             "ending_block":_newparams["beos"]["ending_block"] + self.start_block_nr,
                             "block_interval":_newparams["beos"]["block_interval"]  ,
                             "trustee_reward":_newparams["beos"]["trustee_reward"] } }
            ram_params = {"ram":{  "starting_block":_newparams["ram"]["starting_block"]  + self.start_block_nr,
                             "next_block":_newparams["ram"]["next_block"], 
                             "ending_block":_newparams["ram"]["ending_block"] + self.start_block_nr,
                             "block_interval":_newparams["ram"]["block_interval"]  ,
                             "trustee_reward":_newparams["ram"]["trustee_reward"] } }
            changeparams_distro = patterns.ChangeparamsDistributionAction(asset, beos_params, ram_params, ram_leftover)
            return self.make_action_call(changeparams_distro.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "changeparams"))


    def issue(self, _from, _to, _quantity, _memo, _authorized_by = None):
        try:
            issue = patterns.IssueAction(_from, _to, _quantity, _memo, _authorized_by=_authorized_by)
            return self.make_action_call(issue.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "issue"))


    def withdraw(self, _from, _bts_to, _quantity, _memo, _authorized_by = None):
        try:
            withdraw = patterns.WithdrawAction(_from, _bts_to, _quantity, _memo, _authorized_by=_authorized_by)
            return self.make_action_call(withdraw.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "withdraw"))


    def buyram(self, _payer, _receiver, _quant, _authorized_by = None):
        try:
            buyram = patterns.BuyRamAction(_payer, _receiver, _quant, _authorized_by=_authorized_by)
            return self.make_action_call(buyram.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "buyram"))


    def buyrambytes(self, _payer, _receiver, _bytes, _authorized_by = None):
        try:
            buyrambytes = patterns.BuyRamBytesAction(_payer, _receiver, _bytes, _authorized_by=_authorized_by)
            return self.make_action_call(buyrambytes.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "buyrambytes"))


    def delegatebw(self, _from, _receiver, _stake_net_quantity, _stake_cpu_quantity, _transfer, _authorized_by = None):
        try:
            delegatebw = patterns.DelegatebwAction(_from, _receiver, _stake_net_quantity, _stake_cpu_quantity, _transfer, _authorized_by=_authorized_by)
            return self.make_action_call(delegatebw.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "delegatebw"))


    def regproducer(self, _producer, _producer_key, _url = "", _location = 0, _authorized_by = None):
        try:
            regproducer = patterns.RegproducerAction( _producer, _producer_key, _url, _location, _authorized_by=_authorized_by)
            return self.make_action_call(regproducer.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "regproducer"))

    def unregprod(self, _producer, _authorized_by = None):
        try:
            unregprod = patterns.UnregprodAction( _producer, _authorized_by=_authorized_by)
            return self.make_action_call(unregprod.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "unregprod"))

    def sellram(self, _account, _bytes, _authorized_by = None):
        try:
            sellram = patterns.SellramAction(_account, _bytes, _authorized_by=_authorized_by)
            return self.make_action_call(sellram.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "sellram"))


    def transfer(self, _from, _to, _quantity, _memo, _authorized_by = None):
        try:
            transfer = patterns.TransferAction(_from, _to, _quantity, _memo, _authorized_by=_authorized_by)
            return self.make_action_call(transfer.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "transfer"))


    def undelegatebw(self, _from, _receiver, _unstake_net_quantity, _unstake_cpu_quantity, _authorized_by = None):
        try:
            undelegatebw = patterns.UndelegatebwAction(_from, _receiver, _unstake_net_quantity, _unstake_cpu_quantity, _authorized_by=_authorized_by)
            return self.make_action_call(undelegatebw.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "undelegatebw"))


    def voteproducer(self, _voter, _proxy, _producers, _authorized_by = None):
        try:
            voteproducer = patterns.VoteproducerAction(_voter, _proxy, _producers, _authorized_by=_authorized_by)
            return self.make_action_call(voteproducer.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "voteproducer"))


    def create_account(self, _name, _activ_key = None, _owner_key = None,  _init_ram = True, _authorized_by = None, _creator = None,):
        try:
            if not _creator:
                _creator = "beos.gateway"
            if not _activ_key:
                _activ_key = self.utils.create_key()
            if not _owner_key:
                _owner_key = self.utils.create_key()
            create_account = patterns.CreateAccountAction(_creator, _name, _owner_key, _activ_key, _init_ram)
            return self.make_action_call(create_account.make_action())
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}` action.".format(str(_ex), "create_account"))


    def wait_till_block(self, _block):
        try:
            while self.start_block_nr + _block  > int(self.utils.get_info()["head_block_num"]):
                time.sleep(0.5)
                continue
            pass
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}`.".format(str(_ex), "wait_till_block"))


    def wait_n_blocks(self, _blocks_to_wait):
        try:
            start = int(self.utils.get_info()["head_block_num"])
            while (start + _blocks_to_wait) > int(self.utils.get_info()["head_block_num"]):
                time.sleep(0.5)
                continue
            pass
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}`.".format(str(_ex), "wait_till_block"))

    
    def wait_for_transaction_in_block(self, _transaction_id):
        try:
            max_intervals = 0
            while max_intervals < MAX_WAIT_INTERVALS:
                block_num = {"head_block_num" : int(self.utils.get_info()["head_block_num"])}
                block_data = self.utils.get_block(block_num, True)
                for transaction in block_data["transactions"]:
                    status = transaction.get("status", None)
                    trx = transaction.get("trx", None)
                    if trx is not None and status == "executed":
                        tid = trx.get("id", None)
                        if tid is not None and tid == _transaction_id:
                            log.info("Transaction id: {0} found in block: {1}".format(_transaction_id, block_num))
                            log.info(block_data)
                            return block_num["head_block_num"]
                time.sleep(0.5)
                max_intervals += 1
            if max_intervals >= MAX_WAIT_INTERVALS:
                raise TimeoutError("Timeout reached. Waited {} blocks".format(MAX_WAIT_INTERVALS))

        except Exception as _ex:
            log.exception("Exception `{0}` while `{1}`.".format(str(_ex), "wait_for_transaction_in_block"))


    def make_cleos_call(self, _params):
        try:
            return self.cleos.make_call(_params)
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}`.".format(str(_ex), "make_cleos_call"))

    def get_url_caller(self):
        try:
            return self.url
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}`.".format(str(_ex), "make_url_call"))


    def make_action_call(self, _action):
        try:
            account = _action["code"]
            actor = _action.pop("authorized_by","")
            action = {_action["action"]:_action}
            delay_block, resp = eosio_rpc_actions.push_action(account,actor,action,"active",True)
            if delay_block:
                self.delay_block += delay_block
            if "transaction_id" in resp:
                log.info("[ACTION][OK] `%s` pushed to block `%d (delay %d)`"%(_action, resp["processed"]["block_num"], self.delay_block))
                return ActionResult(True, "", resp, _action)
            else:
                log.error("[ACTION][ERROR] failed to push action `%s` to block because %s"%(_action, resp["error"]["details"][0]["message"]))
                return ActionResult(False, resp["error"]["details"], resp, _action)
        except Exception as _ex:
            log.exception("Exception `{0}` occures during `{1}`.".format(str(_ex), "make_action_call"))
            return ActionResult(False, "", "", _action)
