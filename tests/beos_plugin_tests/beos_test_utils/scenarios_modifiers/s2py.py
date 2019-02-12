#!/usr/bin/python3 

import os
import re
import six
import sys
import json
import stat
import inspect
import argparse
import datetime 


sys.path.append("../beos_test_utils")

import summarizer

from beosnode      import BEOSNode


common_test_pattern = """#!/usr/bin/python3

# Scenario based on test : {0}

import os
import sys
import time
import datetime 

if __name__ == "__main__":
\tcurrentdir = os.path.dirname(os.path.abspath(__file__))
\tparentdir = os.path.dirname(os.path.dirname(currentdir))
\tsys.path.append(parentdir+"/beos_test_utils")

\tfrom logger        import log
\tfrom beosnode      import BEOSNode
\tfrom summarizer    import *
\tfrom cmdlineparser import parser
\targs = parser.parse_args()
\tnode = BEOSNode(args.nodeos_ip, args.nodeos_port, args.keosd_ip,
\t\targs.keosd_port, args.master_wallet_name, args.path_to_cleos, args.path_to_keosd, int(args.scenario_multiplier))

\tnode.run_node(currentdir+r"/node/{0}/", currentdir+r"/logs/{0}/")
\tsummary = Summarizer(currentdir+r"/{0}")\n
\tadd_handler(currentdir+r"/logs/{0}/{0}")\n
"""

actions = {
    "buyram" : BEOSNode.buyram,
    "buyrambytes" : BEOSNode.buyrambytes,
    "params" : BEOSNode.changeparams, 
    "newaccount_pattern" : BEOSNode.create_account,
    "delegatebw" : BEOSNode.delegatebw,
    "issue" : BEOSNode.issue,
    "regproducer" : BEOSNode.regproducer,
    "sellram" : BEOSNode.sellram,
    "transfer" : BEOSNode.transfer,
    "undelegatebw" : BEOSNode.undelegatebw,
    "voteproducer" : BEOSNode.voteproducer,
    "withdraw" : BEOSNode.withdraw
}

summary = {
    "action":summarizer.ActionResult,
    "resources":summarizer.ResourceResult,
    "voter_info":summarizer.VotersResult
}


parser = argparse.ArgumentParser()
parser.add_argument('--counter-prefix', help ="Set how many leading `0` should be before generated scenarios.", default=3)
parser.add_argument('--scenarios-to-transform', help="Set name of file with scenarios [default=scenarions_to_transfer.json]", default="scenarions_to_transfer.json" )

def add_changeparams(_params):
    node_asset           = "[\"{0}\"]".format("0.0000 BTS")
    node_witnes_election = "{0}".format(_params["starting_block_for_initial_witness_election"]) 
    node_beos = "[{0},{1},{2},{3},{4}]".format(_params["starting_block_for_beos_distribution"],
                                               0,
                                               _params["ending_block_for_beos_distribution"],
                                               _params["distribution_payment_block_interval_for_beos_distribution"],
                                               _params["trustee_reward_beos"])
    node_ram = "[{0},{1},{2},{3},{4}]".format(_params["starting_block_for_ram_distribution"],
                                               0,
                                               _params["ending_block_for_ram_distribution"],
                                               _params["distribution_payment_block_interval_for_ram_distribution"],
                                               _params["trustee_reward_ram"])
    node_leftover = "{0}".format(_params["distrib_ram_leftover"])

    new_file_str = "\tnode.changeparams({0}, {1}, {2}, {3}, {4})\n".format(node_asset, node_witnes_election, node_beos, node_ram, node_leftover)
    return new_file_str

def add_actions_and_results(_actions, _results):
    def prepare_actions(_actions):
        actions = []
        all_actions  = _actions
        many_actions = []
        for action in all_actions:
            if isinstance(action, list):
                many_actions.append(action)
            else:
                actions.append(action)
        actions = sorted(actions, key=lambda k: k['start_block'])
        if many_actions:
            many_actions = sorted(many_actions, key=lambda k: k[0]['start_block'])
            many_actions = many_actions[0]
            start_block = many_actions[0]['start_block']
            inserted = False
            for index, action in enumerate(actions):
                if action['start_block'] >= start_block:
                    actions.insert(index, many_actions)
                    inserted = True
                    break
            if not inserted:
                actions.append(many_actions)
        return actions

    def prepare_results(_results):
        for result in _results:
            user = result["user"]
            for after_block in result["after_block"]:
                after_block["user"]=user
                after_block["start_block"]=after_block.pop("after_block")
        return _results
    
    def add_action(_action):
        start_block = _action["start_block"]
        action_summ = "\tnode.wait_till_block({0})\n".format(start_block)
        if "action" in _action:
            action_name = _action["action"]
            action_func = actions[action_name].__name__
            sig  = inspect.getargspec(actions[action_name])
            args = "("
            if action_name == "newaccount_pattern":
                args += "\"" + _action["name"] + "\""
            else:
                for s in sig[0]:
                    for a in _action["args"]:
                        if a == s[1:]:
                            if isinstance(_action["args"][a], six.string_types):
                                args += "{0}=\"{1}\",".format(s,_action["args"][a])
                            else:
                                args += "{0}={1},".format(s,_action["args"][a])
                #lately, there was `_from` keyword added, we need to check if it remain
                reduced = [ s for s in sig[0] if s[1:] not in _action["args"]]
                if reduced:
                    if "_from" in reduced:
                        args += "{0}=\"{1}\",".format("_from",_action["authorized_by"])
                    if "_memo" in reduced:
                        args += "{0}=\"{1}\",".format("_memo", "_memo")
            if args.endswith(","):
                args = args[:-1] 
            args += ")"
            action_func_call = "{0}{1}".format(action_func, args)
            if "expected_result" in _action:
                expected = "ActionResult({0}, \"{1}\")".format(_action["expected_result"]["status"], _action["expected_result"]["message"])
            else:
                expected = "ActionResult(True, \"\")"
            action_summ += "\tsummary.action_status(node.{0}, {1} )\n".format(action_func_call, expected)
        else:
            action_summ += add_results(_action["user"], _action)
        return action_summ
        
    mod= prepare_results(_results)
    for m in mod:
        _actions.extend(m["after_block"])
    summary = ""
    all_actions = prepare_actions(_actions)
    for action in all_actions:
        summary += add_action(action)

    return summary

def add_results(_user, _results):
    def add_result(_action, _what ):
        args = "{0}(".format(_action)
        sig = inspect.getargspec(summary[_what])
        for s in sig[0]:
            for a in at_end[_what]:
                if a == s[1:]:
                    if isinstance(at_end[_what][a], six.string_types):
                        args += "{0}=\"{1}\",".format(s,at_end[_what][a])
                    else:
                        args += "{0}={1},".format(s,at_end[_what][a])
        if args.endswith(","):
            args = args[:-1] + ")"
        return "\tsummary.user_block_status({0}, \"{1}\", {2})\n".format("node", user, args)

    end_summary =""
    if _results:
        user   = _user
        at_end = _results
        if user :
            if "resources" in _results:
                end_summary += add_result("ResourceResult", "resources")
            if "voter_info" in _results:
                end_summary += add_result("VotersResult", "voter_info")
        return  end_summary
    else:
        return "\n\t"

def transform_to_py(_scenario):
    name    = _scenario["name"]
    name    = name.replace(" ", "-")
    while name.endswith('.'):
        name = name[:-1]
    params  = _scenario["params"]
    actions = _scenario["actions"]
    results = _scenario["expected_results"]

    

    new_file_str = common_test_pattern.format(name)

    new_file_str += "\t\n"
    new_file_str += "\t#Changeparams\n"
    new_file_str += add_changeparams(params)
    new_file_str += "\t\n"
    new_file_str += "\t#Actions\n"
    new_file_str += add_actions_and_results(actions, results)
    new_file_str += "\t\n"
    new_file_str += "\t#At end\n"
    for data in results:
        new_file_str += add_results(data["user"], data["at_end"])

    return new_file_str

if __name__ == "__main__":
    args = parser.parse_args()
    with open(args.scenarios_to_transform, "r") as scenarios:
        string=scenarios.read()
        counter = 0
        counter_prefix= args.counter_prefix
        file_name_prefix = "scenario_"
        file_name_ext = ".py"
        all_scenarios = json.loads(string)["scenarios"]

        for scenario in all_scenarios:
            save_scenario = scenario
            save_scenario_str = transform_to_py(save_scenario)
            print(save_scenario_str)
            counter_str = (counter_prefix-len(str(counter)))*"0" + str(counter)
            scenario_name = scenario["name"]
            scenario_name = scenario_name.replace(' ','_')
            if scenario_name.endswith('.'):
                scenario_name = scenario_name[:-1]

            tester_id = re.findall('\[[0-9]+.[0-9]+\]',scenario_name)
            if tester_id:
                tester_id = tester_id[0][1:tester_id[0].find('.')]
            else:
                print("Invalid scenario name. Scenario name must contain tester id! (example [1.1])", scenario_name)
                exit(1)
            
            scenario_file_name = counter_str+"_"+scenario_name+"_"+file_name_ext
            
            while os.path.isfile(scenario_file_name):
                scenario_file_name += "_"
                
            whole_path = os.getcwd() + '/' + "scenarios_tester_" + tester_id
            if not os.path.exists(whole_path):
                os.makedirs(whole_path)
            whole_path += '/' + scenario_file_name
            with open(whole_path, "a+") as split_scenario_name:
                split_scenario_name.writelines(save_scenario_str)
                counter += 1
                st = os.stat(whole_path)
                os.chmod(whole_path, st.st_mode | 0o111)