import json
import time
import threading 
import requests
import datetime

from eosrpcexecutor import EOSRPCExecutor

class TestScenarios(object):
    def __init__(self, _nodeos_addres, _nodeos_port, _wallet_address, _wallet_port, _scenarios_file_name, _append_start_block):
        self.summary_file = "Scenarios_summary_"+str(datetime.datetime.now())[:-7]
        self.scenarios_file = _scenarios_file_name
        self.actions      = None
        self.after_block  = {}
        self.scenarios    = None
        self.scenariosNr  = None
        self.blockNumber  = 0
        self.after_block_result    = {}
        self.called_actions_result = {}
        self.eos_rpc      = EOSRPCExecutor(_nodeos_addres, _nodeos_port, _wallet_address, _wallet_port)
        self.join_block_number = int(self.eos_rpc.get_info()["head_block_num"]) if _append_start_block else 0
        print("self.join_block_number",self.join_block_number)
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
        while self.runScenarios.is_set():
            while self.askForBlockNumber.is_set():
                blockNumber = self.eos_rpc.get_info()
                self.blockNumber = int(blockNumber["head_block_num"])
                time.sleep(0.25)
            self.blockNumber = 0


    def load_scenarios(self):
        try:
            with open(self.scenarios_file) as scenarios:
                self.scenarios = json.load(scenarios)["scenarios"]
        except Exception as _ex:
            print("Error while loading scenarios ", str(_ex))
            exit(1)


    def get_action_calls_summary(self, _file):
        actions = self.eos_rpc.get_actions_call_summary()
        _file.writelines("[INFO] CHECKING ACTION CALL SUMMARY \n")
        error = False
        for action in actions:
            act      = action[0]
            expected = action[1]
            status   = action[2]
            if expected == status:
                _file.writelines("[OK] action %s status call is as expected %d"%(act, expected))
            else:
                _file.writelines("[ERROR] action %s status call % is not as expected %d"%(act, status ,expected))
                error = True
            _file.writelines('\n')
        _file.writelines("###################################\n")
        self.eos_rpc.clear_actions_call_summary()
        return error


    def get_at_end_summary(self, _file, _symbol):
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


    def get_after_block_summary(self, _file):
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
                                   _file.writelines("[INFO] CHECKING VALUES FOR `AFTER BLOCK` %d\n"%value)
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


    def get_scenario_summary(self, _symbol="PXBTS"):
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


    def wait_for_end(self):
        scenario_block = self.scenarios[self.scenariosNr]["scenario_blocks"]
        while scenario_block >= self.blockNumber:
            time.sleep(0.5)


    def set_scenario_params(self):
        params = self.scenarios[self.scenariosNr]["params"]
        self.eos_rpc.prepare_and_push_transaction(params)


    def make_scenario_actions(self):
        self.set_scenario_params()
        return self.execute_scenatio_actions()


    def stop_scenarios(self):
        self.runScenarios.clear()
        self.askForBlockNumber.clear()


    def check_user_status_after_block(self, _symbol="PXBTS"):
        while self.runScenarios.is_set():
            while self.askForBlockNumber.is_set():
                if self.after_block:
                    for user, after_blocks in self.after_block.items():
                        if after_blocks and self.blockNumber > (after_blocks[0]["after_block"]  ):
                            after_block = (after_blocks[0]["after_block"]  )
                            after_blocks.pop(0)
                            if self.blockNumber >= (self.scenarios[self.scenariosNr]["scenario_blocks"]  ):
                                return
                            balance = self.eos_rpc.get_currency_balance(user, _symbol)
                            account_after_block = self.eos_rpc.get_account(user)
                            result = account_after_block["total_resources"] if "total_resources" in account_after_block else None
                            if result and "owner" in result:
                                result.pop("owner")
                            result["balance"]=balance["balance"]
                            result["after_block"] = (after_block  )
                            if user in self.after_block_result:
                                self.after_block_result[user].append(result)
                            else:
                                self.after_block_result[user] = [result]


    def execute_scenatio_actions(self):
        if not self.askForBlockNumber.is_set():
            self.askForBlockNumber.set()
        if self.actions:
            for action in self.actions:
                if isinstance(action, list):
                    startBlock = (action[0].pop("start_block")  )
                else:
                    startBlock = (action.pop("start_block")  )
                while startBlock and (startBlock + self.join_block_number) >= self.blockNumber:
                    if self.blockNumber >= (self.scenarios[self.scenariosNr]["scenario_blocks"] + self.join_block_number):
                        return
                    time.sleep(0.1)
                if self.blockNumber >= (self.scenarios[self.scenariosNr]["scenario_blocks"] + self.join_block_number):
                    return

                self.eos_rpc.push_action(action)
        else:
            print("There are no actions.")


    def prepare_data(self):
        self.actions     = sorted(self.scenarios[self.scenariosNr]["actions"], key=lambda k: k['start_block'])
        after_block = self.scenarios[self.scenariosNr]["expected_results"]
        for after in after_block:
            if after["user"] in self.after_block:
                for a in after["after_block"]:
                    self.after_block[after["user"]].append(a)    
            else:
                self.after_block[after["user"]]=after["after_block"]
        for key, value in self.after_block.items():
            self.after_block[key] = sorted(value, key=lambda k:k['after_block'])

