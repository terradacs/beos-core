import json
import time
import threading 
import requests
import datetime

from logger import log
from eosrpcexecutor import EOSRPCExecutor

class TestScenarios(object):
    def __init__(self, _nodeos_addres, _nodeos_port, _wallet_address, _wallet_port, _scenarios_file_name, _append_start_block):
        self.summary_file = "Scenarios_summary_"+str(datetime.datetime.now())[:-7]
        self.scenarios_file = _scenarios_file_name
        self.actions      = []
        self.after_block  = {}
        self.scenarios    = None
        self.scenariosNr  = None
        self.blockNumber  = 0
        self.after_block_result    = {}
        self.called_actions_result = {}
        self.eos_rpc      = EOSRPCExecutor(_nodeos_addres, _nodeos_port, _wallet_address, _wallet_port)
        self.join_block_number = int(self.eos_rpc.get_info()["head_block_num"]) if _append_start_block else 0
        log.info("self.join_block_number%d"%self.join_block_number)
        self.load_scenarios()

        self.blockGetter = threading.Thread(target=self.block_id_getter)
        self.blockGetter.setDaemon(daemonic=True)
        self.user_status_getter = threading.Thread(target=self.check_user_status_after_block)
        self.user_status_getter.setDaemon(daemonic=True)
        self.runScenarios = threading.Event()
        self.runScenarios.set()
        self.askForBlockNumber = threading.Event()
        self.blockGetter.start()
        self.user_status_getter.start()
        

    def __iter__(self):
        return self

   
    def __next__(self):
        if self.scenariosNr == None:
            self.scenariosNr = 0
        else:
            self.scenariosNr += 1
            if self.scenariosNr == len(self.scenarios):
                raise StopIteration
        return self


    def get_current_scenario(self):
        if self.scenarios:
            return self.scenarios[self.scenariosNr]["name"]
        else:
            return "Scenarios was not even inited."

 
    def block_id_getter(self):
        try:
            while self.runScenarios.is_set():
                while self.askForBlockNumber.is_set():
                    blockNumber = self.eos_rpc.get_info()
                    self.blockNumber = int(blockNumber["head_block_num"])
                    time.sleep(0.25)
                self.blockNumber = 0
        except Exception as _ex:
            log.error("Exception `%s` while getting block id."%(str(_ex)))
            self.stop_scenarios()
            exit(1)


    def load_scenarios(self):
        try:
            with open(self.scenarios_file) as scenarios:
                self.scenarios = json.load(scenarios)["scenarios"]
        except Exception as _ex:
            log.error("Exception `%s` while loading scenarios "%str(_ex))
            self.stop_scenarios()
            exit(1)


    def comare_expected_messages(self, _expected_result, _details ):
        same_status  = False
        same_message = False
        expected_status = _expected_result["status"]
        #at this level, only errors have messages
        if "message" in _expected_result:
            if expected_status == False:
                same_status = True
            else:
                if expected_status == True:
                    same_status = True
        else:
            if expected_status == True:
                same_status = True

        expected_messag = _expected_result["message"] if "message" in _expected_result else ""
        if expected_messag:
            for detail in _details:
                msg = detail["message"]
                if expected_messag.lower() in msg.lower():
                    same_message = True
                    break
        else:
            same_message = True

        return (same_status, same_message, expected_messag)


    def get_action_calls_summary(self, _file):
        try:
            actions = self.eos_rpc.get_actions_call_summary()
            _file.writelines("[INFO] CHECKING ACTION CALL SUMMARY \n")
            error = False
            for action in actions:
                act      = action[0]
                expected = action[1]
                status   = action[2]
                if not isinstance(status, bool):
                    same_status, same_message, message = self.comare_expected_messages(expected, status)
                    if same_status:
                        if same_message:
                            _file.writelines("[OK] action `%s` status call and message are as expected."%(act))
                        else:
                            _file.writelines("[ERROR] action `%s` status call is as expected `%d` but message `%s` is not."%(act, expected["status"], message))
                    else:
                        if same_message:
                            _file.writelines("[ERROR] action `%s` status call is not as expected `%d` but message is."%(act, expected["status"]))
                        else:
                            _file.writelines("[ERROR] action `%s` status call is not as expected `%d` as well as message `%s`."%(act, expected["status"], message))
                else:
                    if expected["status"] == status:
                        _file.writelines("[OK] action `%s` status call is as expected `%d`."%(act, expected["status"]))
                    else:
                        _file.writelines("[ERROR] action `%s` status call `%d` is not as expected `%d`."%(act, status ,expected["status"]))
                        error = True
                _file.writelines('\n')
            _file.writelines("###################################\n")
            self.eos_rpc.clear_actions_call_summary()
            return error
        except Exception as _ex:
            log.error("Exception `%s` while getting scenarios action calls summary"%str(_ex))
            self.stop_scenarios()
            exit(1)


    def get_at_end_summary(self, _file, _symbol):
        try:
            expected_result_for_user = self.scenarios[self.scenariosNr]["expected_results"]
            for expected in expected_result_for_user:
                user = expected["user"]
                balance = self.eos_rpc.get_currency_balance(user, _symbol)
                result = self.eos_rpc.get_account(user)
                total_resources = result["total_resources"] if "total_resources" in result else None
                total_resources["balance"]=balance["balance"]
                at_end = expected["at_end"] if "at_end" in expected else None
                error = False
                if total_resources and at_end:
                    _file.writelines("[INFO] CHECKING `AT END` VALUES FOR ACCOUNT %s\n"%(user))
                    for key, value in at_end.items():
                        if at_end[key] == total_resources[key]:
                            _file.writelines("[OK] VALUE FOR %s IS AS EXPECTED \n"%(key))
                        else:
                            _file.writelines("[ERROR] VALUE %s FOR %s DOES NOT MATCH EXPECTED ONE %s\n"%( total_resources[key], key, at_end[key]))
                            error = True
                else:
                    if not total_resources and not at_end:
                        _file.writelines("[OK] BOTH `AT_END` AND `TOTAL_RESOURCES` ARE NOT AVAILABLE FOR %s \n"%(user))
                    if total_resources:
                        error = True
                        _file.writelines("[ERROR] `AT_END` IS NOT DEFINED FOR USER %s WHILE `TOTAL_RESOURCES` IS AVAILABLE\n"%(user))
                    if at_end:
                        error = True
                        _file.writelines("[ERROR] `TOTAL_RESOURCES` IS NOT DEFINED FOR USER %s WHILE `AT_END` IS AVAILABLE\n"%(user))
                if not error:
                    _file.writelines("[OK] ALL VALUES FOR %s ARE OK\n"%(user))
            _file.writelines("###################################\n")
            return error
        except Exception as _ex:
            log.error("Exception `%s` while getting scenarios end summary"%str(_ex))
            self.stop_scenarios()
            exit(1)  


    def get_after_block_summary(self, _file):
        try:
            error = False
            expected_result_for_user = self.scenarios[self.scenariosNr]["expected_results"]
            for expected in expected_result_for_user:
                user = expected["user"]
                if "after_block" in expected:
                    _file.writelines("[INFO] CHECKING `AFTER BLOCKS` VALUES FOR ACCOUNT %s\n"%(user))
                    for expected_after_block in expected["after_block"]:
                        for actual_after_block in self.after_block_result[user]:
                            if expected_after_block["after_block"] == actual_after_block["after_block"]:
                                for key, value in expected_after_block.items():
                                    if key == "after_block":
                                        _file.writelines("[INFO] CHECKING VALUES FOR `AFTER BLOCK` %d\n"%(value+self.join_block_number))
                                        _file.writelines("###################################\n")
                                        continue
                                    if actual_after_block[key] == expected_after_block[key]:
                                        _file.writelines("[OK] VALUE FOR %s IS AS EXPECTED \n"%(key))
                                    else:
                                        _file.writelines("[ERROR] VALUE %s FOR %s DOES NOT MATCH EXPECTED ONE %s\n"%( actual_after_block[key], key, expected_after_block[key]))
                                        error = True
            _file.writelines("###################################\n")
            self.after_block_result.clear()
            return error
        except Exception as _ex:
            log.error("Exception `%s` while getting scenarios after block summary"%str(_ex))
            self.stop_scenarios()
            exit(1)


    def get_scenario_summary(self, _symbol="PXBTS"):
        try:
            self.askForBlockNumber.clear()
            with open(self.summary_file,"a+") as sf:
                sf.writelines("[SCENARIO] :%s\n"%(self.scenarios[self.scenariosNr]["name"]))
                sf.writelines("############# SUMMARY #############\n")
                actions_error     = self.get_action_calls_summary(sf)
                after_block_error = self.get_after_block_summary(sf)
                at_end_error      = self.get_at_end_summary(sf, _symbol)
                if actions_error or after_block_error or at_end_error:
                    return True
                else :
                    return False
        except Exception as _ex:
            log.error("Exception `%s` while getting scenarios summary"%str(_ex))
            self.stop_scenarios()
            exit(1)


    def wait_for_end(self):
        scenario_block = self.scenarios[self.scenariosNr]["scenario_blocks"]
        log.info("This scenario wait till blocks %d"%(scenario_block+self.join_block_number))
        while (scenario_block + self.join_block_number) >= self.blockNumber:
            time.sleep(0.5)
            if not self.askForBlockNumber.is_set():
                break


    def set_scenario_params(self):
        try:
            params = self.scenarios[self.scenariosNr]["params"]
            if self.join_block_number:
                new_params   = params["args"]["new_params"]
                distribution = new_params[2]
                distribution[0] = distribution[0]+self.join_block_number
                distribution[1] = distribution[1]+self.join_block_number
                ram          = new_params[3]
                ram[0] = ram[0]+self.join_block_number
                ram[1] = ram[1]+self.join_block_number
                trustee      = new_params[4]
                trustee[0] = trustee[0]+self.join_block_number
                trustee[1] = trustee[1]+self.join_block_number
            self.eos_rpc.prepare_and_push_transaction(params)
        except Exception as _ex:
            log.error("Exception `%s` while setting scenarios params"%str(_ex))
            self.stop_scenarios()
            exit(1)


    def make_scenario_actions(self):
        try:
            self.set_scenario_params()
            return self.execute_scenatio_actions()
        except Exception as _ex:
            log.error("Exception `%s` while making scenarios actions"%str(_ex))
            self.stop_scenarios()
            exit(1)


    def stop_scenarios(self):
        try:
            self.runScenarios.clear()
            self.askForBlockNumber.clear()
            self.eos_rpc.clear_action_flag()
        except Exception as _ex:
            log.error("Exception `%s` while stoping scenarios"%str(_ex))
            exit(1)


    def check_user_status_after_block(self, _symbol="PXBTS"):
        try:
            while self.runScenarios.is_set():
                while self.askForBlockNumber.is_set():
                    if self.after_block:
                        for user, after_blocks in self.after_block.items():
                            if after_blocks and self.blockNumber > (after_blocks[0]["after_block"] + self.join_block_number ):
                                after_block = (after_blocks[0]["after_block"]  )
                                after_blocks.pop(0)
                                if self.blockNumber >= (self.scenarios[self.scenariosNr]["scenario_blocks"] + self.join_block_number ):
                                    return
                                balance = self.eos_rpc.get_currency_balance(user, _symbol)
                                account_after_block = self.eos_rpc.get_account(user)
                                result = account_after_block["total_resources"] if "total_resources" in account_after_block else {}
                                if result and "owner" in result:
                                    result.pop("owner")
                                result["balance"]=balance["balance"]
                                result["after_block"] = (after_block  )
                                if user in self.after_block_result:
                                    self.after_block_result[user].append(result)
                                else:
                                    self.after_block_result[user] = [result]
        except Exception as _ex:
            log.error("Exception `%s` while checking user status after block"%str(_ex))
            self.stop_scenarios()
            exit(1)


    def execute_scenatio_actions(self):
        try:
            if not self.askForBlockNumber.is_set():
                self.askForBlockNumber.set()
            if self.actions:
                for action in self.actions:
                    if isinstance(action, list):
                        startBlock = (action[0].pop("start_block")  )
                    else:
                        startBlock = (action.pop("start_block")  )
                    while startBlock and (startBlock + self.join_block_number) >= (self.blockNumber ):
                        if self.blockNumber >= (self.scenarios[self.scenariosNr]["scenario_blocks"] + self.join_block_number):
                            return
                        if not self.askForBlockNumber.isSet():
                            break
                        time.sleep(0.1)
                    if self.blockNumber >= (self.scenarios[self.scenariosNr]["scenario_blocks"] + self.join_block_number):
                        return

                    self.eos_rpc.push_action(action)
            else:
                log.info("There are no actions.")
                exit(0)
        except Exception as _ex:
            log.error("Exception `%s` while executing scenarios actions"%str(_ex))
            self.stop_scenarios()
            exit(1)


    def prepare_actions(self):
        try:
            self.actions.clear()
            all_actions  = self.scenarios[self.scenariosNr]["actions"]
            many_actions = []
            for action in all_actions:
                if isinstance(action, list):
                    many_actions.append(action)
                else:
                    self.actions.append(action)
            self.actions = sorted(self.actions, key=lambda k: k['start_block'])
            if many_actions:
                many_actions = sorted(many_actions, key=lambda k: k[0]['start_block'])
                many_actions = many_actions[0]
                start_block = many_actions[0]['start_block']
                inserted = False
                for index, action in enumerate(self.actions):
                    if action['start_block'] >= start_block:
                        self.actions.insert(index, many_actions)
                        inserted = True
                        break
                if not inserted:
                    self.actions.append(many_actions)
        except Exception as _ex:
            log.error("Exception `%s` while preparing actions."%str(_ex))
            self.stop_scenarios()
            exit(1)


    def prepare_after_block(self):
        try:
            after_block = self.scenarios[self.scenariosNr]["expected_results"]
            for after in after_block:
                if after["user"] in self.after_block:
                    for a in after["after_block"]:
                        self.after_block[after["user"]].append(a)    
                else:
                    self.after_block[after["user"]]=after["after_block"]
            for key, value in self.after_block.items():
                self.after_block[key] = sorted(value, key=lambda k:k['after_block'])
        except Exception as _ex:
            log.error("Exception `%s` while preparing after blocks."%str(_ex))
            self.stop_scenarios()
            exit(1)


    def prepare_data(self):
        try:
            self.prepare_actions()
            self.prepare_after_block()
        except Exception as _ex:
            log.error("Exception `%s` while preparing scenario data"%str(_ex))
            self.stop_scenarios()
            exit(1)

    def restore_node_params(self,
                _starting_block_for_initial_witness_election,
                _starting_block_for_beos_distribution,
                _ending_block_for_beos_distribution,
                _distribution_payment_block_interval_for_beos_distribution,
                _amount_of_reward_beos,
                _starting_block_for_ram_distribution,
                _ending_block_for_ram_distribution,
                _distribution_payment_block_interval_for_ram_distribution,
                _amount_of_reward_ram,
                _starting_block_for_trustee_distribution,
                _ending_block_for_trustee_distribution,
                _distribution_payment_block_interval_for_trustee_distribution,
                _amount_of_reward_trustee):
        try:
            params={
                    "authorized_by":"beos.init",
                    "code":"beos.init",
                    "action":"changeparams",
                    "args":{
                        "new_params":["0.0000 PXBTS", _starting_block_for_initial_witness_election,
                                                        [ _starting_block_for_beos_distribution,
                                                        _ending_block_for_beos_distribution,
                                                        _distribution_payment_block_interval_for_beos_distribution,
                                                        _amount_of_reward_beos ]
                                                        ,[ _starting_block_for_ram_distribution,
                                                        _ending_block_for_ram_distribution,
                                                        _distribution_payment_block_interval_for_ram_distribution,
                                                        _amount_of_reward_ram ],
                                                        [ _starting_block_for_trustee_distribution,
                                                        _ending_block_for_trustee_distribution,
                                                        _distribution_payment_block_interval_for_trustee_distribution,
                                                        _amount_of_reward_trustee ]
                                                        ]
                    }
                }

            self.eos_rpc.prepare_and_push_transaction(params)
        except Exception as _ex:
            log.error("Exception `%s` while restoring node original data"%str(_ex))
            self.stop_scenarios()
            exit(1)
