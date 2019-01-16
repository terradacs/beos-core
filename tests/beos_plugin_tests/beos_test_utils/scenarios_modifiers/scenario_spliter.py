#!/usr/bin/env python3

import re
import json
import os.path
import argparse

args = None

parser = argparse.ArgumentParser()
parser.add_argument('--counter-prefix', help ="Set how many leading `0` should be before generated scenarios.", default=6)
parser.add_argument('--split-all', help="Split main scenario file into seperate scenarios", action='store_true', default=False)
parser.add_argument('--split-by-users', help="Split main scenario file into seperate scenarios by users ", action='store_true', default=False)
parser.add_argument('--scenarios-to-split', help="Set name of file with scenarios [default=scenarios_continues.in]", default="scenarios_continues.in.json" )

def split_all():
    pass

def split_by_user():
    pass

if __name__ == "__main__":
    args = parser.parse_args()
    with open(args.scenarios_to_split, "r") as scenarios:
        string=scenarios.read()
        counter = 0
        counter_prefix= args.counter_prefix
        file_name_prefix = "scenario_"
        file_name_ext = ".in"
        all_scenarios = json.loads(string)["scenarios"]

    if args.split_all:
        for scenario in all_scenarios:
            save_scenario ={}
            save_scenario["scenarios"] = [scenario]
            save_scenario_str = json.dumps(save_scenario, indent=4)
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

    if args.split_by_users:
        scenarios_per_users = []
        while all_scenarios:
            scenario = all_scenarios.pop(0)
            scenario_str = json.dumps(scenario, indent=4)
            all_users=[]
            users = re.findall('\$\{(user_.*?)\}', scenario_str)
            if users:
                for user in users:
                    all_users.append(user)
            all_users = list(set(all_users))
            all_users.sort()
            scenarios_per_users.append([all_users,scenario])
        splited_scenarios=[]
        while scenarios_per_users:
            scen = scenarios_per_users.pop(0)
            if not scen[0]:
                continue
            scen_users = scen[0]
            founded = []
            founded.append(scen[1])
            for scenario in scenarios_per_users:
                if [ user for user in scen_users if user in scenario[0] ]:
                    for scen_user in scenario[0]:
                        scen_users.append(scen_user)
                    scenario[0]=[]
                    founded.append(scenario[1])
                    
            splited_scenarios.append(founded)
        for splited in splited_scenarios:
            save_scenario = {}
            save_scenario["scenarios"] = []
            for inner in splited:
                save_scenario["scenarios"].append(inner)
            counter_str = (counter_prefix-len(str(counter)))*"0" + str(counter)
            scenario_file_name = file_name_prefix+counter_str+file_name_ext
            while os.path.isfile(scenario_file_name):
                scenario_file_name += "_"
            save_scenario_str = json.dumps(save_scenario, indent=4)
            with open(scenario_file_name, "a+") as split_scenario_name:
                split_scenario_name.writelines(save_scenario_str)
                counter += 1
            
                
            
