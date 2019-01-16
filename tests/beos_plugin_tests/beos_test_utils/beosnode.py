
import os
import sys
import time
import datetime

try:
    from beos_test_utils import run
except Exception as _ex:
    print("Faild to import run.py script. Please make sure that run ./deploy.py --build-beos. Aborting.")
    exit(1)

import beos_test_utils.beosactionpatterns as patterns

from beos_test_utils.logger               import log
from beos_test_utils.eoscleoscaller       import EOSCleosCaller
from beos_test_utils.eoskeosdcaller       import EOSKeosdCaller
from beos_test_utils.eostransactioncaller import EOSTransactionCaller
from beos_test_utils.summarizer           import ActionResult

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cd_scripts import eosio_rpc_actions
from cd_scripts import eosio_rpc_client


class BEOSNode(object):
    node = "node"

    class BEOSNodeData(object):
        def __init__(self, _node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name):
            self.node_ip     = _node_ip 
            self.node_port   = _node_port
            self.keosd_ip    = _keosd_ip
            self.keosd_port  = _keosd_port
            self.wallet_name = _wallet_name,

    def __init__(self, _node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name, _path_to_cleos, _path_to_keosd, _multi = 2 ):
        self.cleos     = EOSCleosCaller(_node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name, _path_to_cleos)
        self.keosd     = EOSKeosdCaller(_node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name, _path_to_keosd)
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
        self.additiona_prod = {}
        self.delay_block = 0
        self.multi = _multi

    def stop_node(self):
        try:
            if self.node_is_running:
                run.kill_process(self.working_dir+"/run_nodeos_{0}_{1}.pid".format(self.node_number, self.node_name,), "nodeos", self.node_data.node_ip, self.node_data.node_port)
                self.node_is_running = False
        except Exception as _ex:
            log.error("Exception `{0}` occures during stoping node `{1}`".format(str(_ex), self.node_name))

    def add_producer_to_config(self, _producer, _key):
        try:
            self.additiona_prod[_producer]=_key
        except Exception as _ex:
            log.error("Exception `{0}` occures during adding producers`{1}`".format(str(_ex), self.node_name))
        

    def run_node(self, _workdir, _log_path):
        try:
            self.log_path    = _log_path
            self.working_dir = _workdir 
            if not os.path.exists(_workdir):
                os.makedirs(_workdir)
            if not os.path.exists(_log_path):
                os.makedirs(_log_path)

            run.clone_nodeos(_workdir, self.node_number, self.node_name,  self.additiona_prod)
            run.run_custom_nodeos(self.node_number, self.node_name, _workdir, _log_path)
            self.node_is_running = True
            self.start_block_nr = self.utils.get_info()["head_block_num"]
            return self.start_block_nr
        except Exception as _ex:
            log.error("Exception `{0}` occures during initialization of node `{1}`".format(str(_ex), self.node_name))

    def changeparams(self, _asset,  _election_block, _beos_params, _ram_params, _ram_leftover):
        try:
            changeparams_init   = patterns.ChangeparamsInitAction( _election_block * self.multi+self.start_block_nr)
            _beos_params = [ _beos_params[0] * self.multi + self.start_block_nr,
                             _beos_params[1], 
                             _beos_params[2] * self.multi + self.start_block_nr,
                             _beos_params[3] * self.multi ,
                             _beos_params[4] ]
            _ram_params = [ _ram_params[0]  * self.multi + self.start_block_nr,
                             _ram_params[1], 
                             _ram_params[2] * self.multi + self.start_block_nr,
                             _ram_params[3] * self.multi ,
                             _ram_params[4] ]
            changeparams_distro = patterns.ChangeparamsDistributionAction(_asset, _beos_params, _ram_params, _ram_leftover)
            changeparams = [changeparams_init.make_action(),  changeparams_distro.make_action()]
            #self.make_action_call(changeparams)
            self.make_action_call(changeparams[0])
            return self.make_action_call(changeparams[1])
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "changeparams"))


    def issue(self, _from, _to, _quantity, _memo, _authorized_by = None):
        try:
            issue = patterns.IssueAction(_from, _to, _quantity, _memo, _authorized_by=_authorized_by)
            return self.make_action_call(issue.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "issue"))


    def withdraw(self, _from, _bts_to, _quantity, _memo, _authorized_by = None):
        try:
            withdraw = patterns.WithdrawAction(_from, _bts_to, _quantity, _memo, _authorized_by=_authorized_by)
            return self.make_action_call(withdraw.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "withdraw"))


    def buyram(self, _payer, _receiver, _quant, _authorized_by = None):
        try:
            buyram = patterns.BuyRamAction(_payer, _receiver, _quant, _authorized_by=_authorized_by)
            return self.make_action_call(buyram.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "buyram"))


    def buyrambytes(self, _payer, _receiver, _bytes, _authorized_by = None):
        try:
            buyrambytes = patterns.BuyRamBytesAction(_payer, _receiver, _bytes, _authorized_by=_authorized_by)
            return self.make_action_call(buyrambytes.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "buyrambytes"))


    def delegatebw(self, _from, _receiver, _stake_net_quantity, _stake_cpu_quantity, _transfer, _authorized_by = None):
        try:
            delegatebw = patterns.DelegatebwAction(_from, _receiver, _stake_net_quantity, _stake_cpu_quantity, _transfer, _authorized_by=_authorized_by)
            return self.make_action_call(delegatebw.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "delegatebw"))


    def regproducer(self, _producer, _producer_key, _url = "", _location = 0, _authorized_by = None):
        try:
            regproducer = patterns.RegproducerAction( _producer, _producer_key, _url, _location, _authorized_by=_authorized_by)
            return self.make_action_call(regproducer.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "regproducer"))


    def sellram(self, _account, _bytes, _authorized_by = None):
        try:
            sellram = patterns.SellramAction(_account, _bytes, _authorized_by=_authorized_by)
            return self.make_action_call(sellram.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "sellram"))


    def transfer(self, _from, _to, _quantity, _memo, _authorized_by = None):
        try:
            transfer = patterns.TransferAction(_from, _to, _quantity, _memo, _authorized_by=_authorized_by)
            return self.make_action_call(transfer.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "transfer"))


    def undelegatebw(self, _from, _receiver, _unstake_net_quantity, _unstake_cpu_quantity, _authorized_by = None):
        try:
            undelegatebw = patterns.UndelegatebwAction(_from, _receiver, _unstake_net_quantity, _unstake_cpu_quantity, _authorized_by=_authorized_by)
            return self.make_action_call(undelegatebw.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "undelegatebw"))


    def voteproducer(self, _voter, _proxy, _producers, _authorized_by = None):
        try:
            voteproducer = patterns.VoteproducerAction(_voter, _proxy, _producers, _authorized_by=_authorized_by)
            return self.make_action_call(voteproducer.make_action())
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "voteproducer"))


    def create_account(self, _name, _creator = None, _activ_key = None, _owner_key = None,  _init_ram = True, _authorized_by = None):
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
            log.error("Exception `{0}` occures during `{1}` action.".format(str(_ex), "create_account"))


    def wait_till_block(self, _block):
        try:
            while self.start_block_nr + (_block * self.multi) > int(self.utils.get_info()["head_block_num"]):
                time.sleep(0.5)
                continue
            pass
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}`.".format(str(_ex), "wait_till_block"))


    def wait_n_blocks(self, _blocks_to_wait):
        try:
            start = int(self.utils.get_info()["head_block_num"])
            while (start + _blocks_to_wait) > int(self.utils.get_info()["head_block_num"]):
                time.sleep(0.5)
                continue
            pass
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}`.".format(str(_ex), "wait_till_block"))

    def make_cleos_call(self, _params):
        try:
            return self.cleos.make_call(_params)
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}`.".format(str(_ex), "make_cleos_call"))


    def make_keosd_call(self, _params):
        try:
            return self.keosd.make_call(_params)
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}`.".format(str(_ex), "make_keosd_call"))


    def get_url_caller(self, _url, _data = None):
        try:
            return self.url.make_call(_url, _data)
        except Exception as _ex:
            log.error("Exception `{0}` occures during `{1}`.".format(str(_ex), "make_url_call"))


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
            log.error("Exception `{0}` occures during `{1}`.".format(str(_ex), "make_action_call"))
            return ActionResult(False, "", "", _action)
