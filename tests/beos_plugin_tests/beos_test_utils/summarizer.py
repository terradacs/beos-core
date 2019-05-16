import os
import datetime
import threading
import collections

from inspect import getframeinfo, stack

from beos_test_utils.logger import log

class ResultException(Exception):
    def __init__(self, _message):
        self.message = _message

    def __str__(self):
        return "Result exception `{0}`".format(self.message)

class Result(object):
    def __init__(self):
        self.result = {}

    def __getitem__(self, _key):
        return self.result.get(_key, None)

    def get_result(self):
        if self.result:
            return self.result
        else:
            raise ResultException("Empty result given.")

    def compare(self, _to_compare):
        raise ResultException("Compare function not implemented.")

    def parser_node_response(self, _to_parse):
        raise ResultException("Response parser not implemented.")

    def compare_and_print_to_file(self, _key, _actual, _expected, _summary_file):
        if _expected[_key] == None:
            return True
        #if str(_actual[_key]).split(".")[0] == str(_expected[_key]).split(".")[0]:
        if str(_actual[_key]) == str(_expected[_key]):
            _summary_file.writelines("[OK] Value `{0}` for key `{1}` is as expected `{2}`.\n".format(_actual[_key], _key, _expected[_key]))
            return True
        else:
            _summary_file.writelines("[ERROR] Value `{0}` for key `{1}` is not as expected `{2}`.\n".format(_actual[_key], _key, _expected[_key]))
            return False

class ActionResult(Result):
    def __init__(self, _status = None, _message = None, _action_data=None, _verbose = ""):
        super(ActionResult, self).__init__()
        self.action_verbose = _verbose
        self.action_data = _action_data   if _action_data != None else None
        self.result["status"]  = _status  if _status != None else True
        self.result["message"] = _message if _message != None else ""

    def __str__(self):
        return "ActionResult :{0}".format(self.result)

    def compare(self, _to_compare, _summary_file = None):
        same_status  = False
        same_message = False
        if self.result["status"] == _to_compare["status"]:
            same_status = True
        try:
            if "message" in self.result:
                msg = self.result["message"][0]["message"]
        except Exception:
            msg = self.result["message"]
        if _to_compare["message"]:
            if _to_compare["message"].lower() in msg.lower()    \
            or msg.lower()  in _to_compare["message"].lower()  :
                print("msg.lower()", msg.lower())
                print("_to_compare[\"message\"]",_to_compare["message"])
                same_message = True
        else:
            same_message = True
        if _summary_file:
            if same_status and same_message:
                _summary_file.writelines("[OK] Action `{0}` status `{1}` and message `{2}` are as expected.\n".format(self.action_verbose, self.result["status"], msg))
            else:
                if same_status:
                    status =  "`{0}` status is as expected `{1}`".format(self.result["status"], _to_compare["status"]) 
                else:
                    status =  "`{0}` status is not as expected `{1}`".format(self.result["status"], _to_compare["status"])

                if same_message:
                    message = "`{0}` message is as expected `{1}`".format(msg, _to_compare["message"]) 
                else:
                    message = "`{0}` message is not as expected `{1}`".format(msg, _to_compare["message"])

                _summary_file.writelines("[ERROR] Action `{0}` {1} and {2}.\n".format(self.action_verbose, status, message))

        return same_status and same_message

class VotersResult(Result):
    def __init__(self, _owner = None, _proxy = None, _producers = None, _staked = None, _last_vote_weight = None, _proxied_vote_weight = None, _is_proxy = None, _reserved1 = None, _reserved2 = None, _reserved3 = None ):
        super(VotersResult, self).__init__()
        # != To avoid False value which can happen
        self.result["owner"] = _owner
        self.result["proxy"] = _proxy
        self.result["producers"] = _producers
        self.result["staked"] = _staked
        self.result["last_vote_weight"] = _last_vote_weight
        self.result["proxied_vote_weight"] = _proxied_vote_weight
        self.result["is_proxy"] = _is_proxy
        self.result["reserved1"] = _reserved1
        self.result["reserved2"] = _reserved2
        self.result["reserved3"] = _reserved3

    def __str__(self):
        return "VotersResult :{0}".format(self.result)
    
    def compare(self, _to_compare, _summary_file = None):
        owner_res  = self.compare_and_print_to_file("owner", self.result, _to_compare, _summary_file)
        proxy_res  = self.compare_and_print_to_file("proxy", self.result, _to_compare, _summary_file)
        pro_res    = self.compare_and_print_to_file("producers", self.result, _to_compare, _summary_file)
        sta_res    = self.compare_and_print_to_file("staked", self.result, _to_compare, _summary_file)
        las_res    = self.compare_and_print_to_file("last_vote_weight", self.result, _to_compare, _summary_file)
        prox_res   = self.compare_and_print_to_file("proxied_vote_weight", self.result, _to_compare, _summary_file)
        is_pro_res = self.compare_and_print_to_file("is_proxy", self.result, _to_compare, _summary_file)
        res1_res   = self.compare_and_print_to_file("reserved1", self.result, _to_compare, _summary_file)
        res2_res   = self.compare_and_print_to_file("reserved2", self.result, _to_compare, _summary_file)
        res3_res   = self.compare_and_print_to_file("reserved3", self.result, _to_compare, _summary_file)
        return owner_res and proxy_res and pro_res and sta_res and las_res and prox_res and is_pro_res and res1_res and res2_res and res3_res

    def parser_node_response(self, _to_parse):
        voter = _to_parse.get("voter", None)

        if voter:
            return VotersResult(  _owner = voter.get("owner",None)
                                , _proxy = voter.get("proxy",None)
                                , _producers = voter.get("producers",None)
                                , _staked = voter.get("staked",None)
                                , _last_vote_weight = voter.get("last_vote_weight",None)
                                , _proxied_vote_weight = voter.get("proxied_vote_weight",None)
                                , _is_proxy = voter.get("is_proxy",None)
                                , _reserved1 = voter.get("reserved1",None)
                                , _reserved2 = voter.get("reserved2",None)
                                , _reserved3 = voter.get("reserved3",None))
        else:
            return VotersResult()


class ResourceResult(Result):
    def __init__(self, _balance = None, _net_weight = None, _cpu_weight = None, _ram_bytes = None, _core_liquid_balance = None):
        super(ResourceResult, self).__init__()
        self.result["balance"] = _balance
        self.result["net_weight"] = _net_weight
        self.result["cpu_weight"] = _cpu_weight
        self.result["ram_bytes"] = _ram_bytes
        self.result["core_liquid_balance"] = _core_liquid_balance

    def __str__(self):
        return "ResourceResult :{0}".format(self.result)

    def compare(self, _to_compare, _summary_file = None):
        bal_res = self.compare_and_print_to_file("balance", self.result, _to_compare, _summary_file)
        net_res = self.compare_and_print_to_file("net_weight", self.result, _to_compare, _summary_file)
        cpu_res = self.compare_and_print_to_file("cpu_weight", self.result, _to_compare, _summary_file)
        ram_res = self.compare_and_print_to_file("ram_bytes", self.result, _to_compare, _summary_file)
        core_res = self.compare_and_print_to_file("core_liquid_balance", self.result, _to_compare, _summary_file)
        return bal_res and net_res and cpu_res and ram_res and core_res

    def parser_node_response(self, _to_parse):
        resources = _to_parse.get("resources", None)
        if resources:
            return ResourceResult(_balance=resources.get("balance", None)
                                ,_net_weight= resources.get("net_weight", None)
                                ,_cpu_weight= resources.get("cpu_weight", None)
                                ,_ram_bytes= resources.get("ram_bytes", None)
                                ,_core_liquid_balance= resources.get("core_liquid_balance", None)
                                )
        else:
            return ResourceResult()
            
class Summarizer(object):
    def __init__(self, _scenario_name):
        self.prepare_summary_files(_scenario_name)
        
        self.block_summaries  = {}
        self.action_summaries = []
        self.equal_summaries  = []
        self.error_action     = False
        self.error_user_block = False
        self.error_equal      = False


    def prepare_summary_files(self, _scenario_name):
        data = os.path.split(_scenario_name)
        path = data[0] + "/summary/" if data[0] else "./summary/"
        file = data[1]
        self.scenario_name = file 
        if path and not os.path.exists(path):
            os.makedirs(path)
        now = str(datetime.datetime.now())[:-7]
        now = now.replace(' ', '-')
        self.scenario_summary_file  = path+"Summary_"+now+"_"+file+".log"
        self.scenarios_status_file = path+"All_scenarios_status_review.txt"


    def action_status(self, _action, _expected_result = None ):
        if _expected_result:
            self.action_summaries.append([_action, _expected_result ])
        else:
            self.action_summaries.append([_action,  ActionResult(True, "") ])


    def user_block_status(self, _node, _user, _expected_result, _symbol = "BTS"):
        block   = _node.utils.get_info()["head_block_num"]
        result  = _node.utils.get_account(_user)
        balance = _node.utils.get_currency_balance(_user, _symbol)
        voter_info      = result.get("voter_info", {})
        total_resources = result.get("total_resources", {})
        total_resources["core_liquid_balance"] = result.get("core_liquid_balance", "")
        total_resources["balance"] = balance.get("balance","")
        if _user in self.block_summaries:
            self.block_summaries[_user].append({"block":block, "resources":total_resources, "voter":voter_info, "expected":_expected_result})
        else:
            self.block_summaries[_user]=[{"block":block, "resources":total_resources, "voter":voter_info, "expected":_expected_result}]


    def equal(self, _expected_result, _actual_result, _debug_str=None):
        try:
            caller = getframeinfo(stack()[1][0])
            Equal = collections.namedtuple('Equal', ('expected', 'actual', 'line', 'debug'))
            if _debug_str:
                debug_info = _debug_str
            else:
                debug_info = None
        
            self.equal_summaries.append(Equal(_expected_result, _actual_result, caller.lineno, debug_info))
        except Exception as _ex:
            log.exception("Exception `{0}` occurres while equal call.".format(str(_ex)))


    def action_status_summary(self):
        error = False
        if self.action_summaries:
            self.summary.writelines("[ACTIONS SUMMARY]\n")
            self.summary.writelines("-"*30+'\n')
            for actions in self.action_summaries:
                actual   = actions[0]
                expected = actions[1]
                if not actual.compare(expected, self.summary):
                    error = True
            self.summary.writelines("-"*30+'\n')
        return error


    def user_block_summary(self):
        error = False
        if self.block_summaries:
            self.summary.writelines("[USERS BLOCK SUMMARY]\n")
            for user in self.block_summaries.keys():
                self.summary.writelines("-"*30+'\n')
                self.summary.writelines("[SUMMARY FOR USER] {0}\n".format(user))
                for values in self.block_summaries[user]:
                    self.summary.writelines("-"*30+'\n')
                    self.summary.writelines("[AT BLOCK] {0}\n".format(values["block"]))
                    self.summary.writelines("-"*30+'\n')
                    expected = values.pop("expected")
                    actual = expected.parser_node_response(values)
                    if not actual.compare(expected, self.summary):
                        error = True
            self.summary.writelines("-"*30+'\n')
        return error


    def equal_summary(self):
        error = False
        if self.equal_summaries:
            self.summary.writelines("[EQUAL SUMMARY]\n")
            self.summary.writelines("-"*30+'\n')
            for equal in self.equal_summaries:
                if equal.expected == equal.actual:
                    if equal.debug:
                        self.summary.writelines("[OK] Conditions `{0}` result `{1}` from line `{2}` is as expected `{3}`.\n".format(equal.debug, equal.actual,equal.line, equal.expected))
                    else:
                        self.summary.writelines("[OK] Conditions result `{0}` from line `{1}` is as expected `{2}`.\n".format(equal.actual, equal.line, equal.expected))
                else:
                    error = True
                    if equal.debug:
                        self.summary.writelines("[ERROR] Conditions `{0}` result `{1}` from line `{2}` is not as expected `{3}`.\n".format(equal.debug, equal.actual ,equal.line, equal.expected))
                    else:
                        self.summary.writelines("[ERROR] Conditions result `{0}` from line `{1}` is not as expected `{2}`.\n".format( equal.actual, equal.line, equal.expected))
        return error


    def add_scenario_status_to_summary_file(self, _error):
        try:
            with open(self.scenarios_status_file,"a+") as sf:
                temp_len_scen = len(" Scenario name ") 
                max_scenario_name = 100
                if os.stat(self.scenarios_status_file).st_size == 0:
                    sf.writelines(" Scenario name " + (max_scenario_name-temp_len_scen)*' ' + "| status \n")
                    sf.writelines( max_scenario_name*'-' + '|' + len("+ status ")*'-' +'\n')
                log_status = "| {0}".format("ERROR" if _error else "OK")
                sf.writelines(self.scenario_name + (max_scenario_name-len(self.scenario_name))*' ' + log_status + '\n')
        except Exception as _ex:
            log.exception("Exception `%s` while adding scenarios status to summary file."%str(_ex))
            exit(1)


    def summarize(self):
        with open(self.scenario_summary_file, "a+") as self.summary:
            self.summary.writelines("[SCENARIO] {0}\n".format(self.scenario_name))
            self.summary.writelines("-"*30+'\n')
            self.error_action      = self.action_status_summary()
            self.error_user_block  = self.user_block_summary()
            self.error_equal       = self.equal_summary()
            self.add_scenario_status_to_summary_file(self.error_action or self.error_user_block or self.error_equal )
            return self.error_action or self.error_user_block or self.error_equal