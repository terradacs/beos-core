#!/usr/bin/env python3

import re
import json
import os.path
import argparse

args = None

parser = argparse.ArgumentParser()
parser.add_argument('--scenarios-to-fix', help="Set name of file with scenarios [default=scenarios_continues.in]", default="scenarios_continues.json" )

def change_param_format( _old_change_param ):
    new_param = {}
    new_param["starting_block_for_initial_witness_election"] = _old_change_param[1]
    new_param["starting_block_for_beos_distribution"] = _old_change_param[2][0]
    new_param["ending_block_for_beos_distribution"] = _old_change_param[2][1]
    new_param["distribution_payment_block_interval_for_beos_distribution"] = _old_change_param[2][2]
    new_param["trustee_reward_beos"] = _old_change_param[2][3]
    new_param["starting_block_for_ram_distribution"] = _old_change_param[3][0]
    new_param["ending_block_for_ram_distribution"] = _old_change_param[3][1]
    new_param["distribution_payment_block_interval_for_ram_distribution"] = _old_change_param[3][2]
    new_param["trustee_reward_ram"] = _old_change_param[3][3]
    new_param["distrib_ram_leftover"] = 3000000
    return new_param

if __name__ == "__main__":
    args = parser.parse_args()
    with open(args.scenarios_to_fix, "r") as scenarios:
        string=scenarios.read()
        file_name_prefix = args.scenarios_to_fix+"_fix"
        file_name_ext = ".in"
        fixed_scenario = file_name_prefix+file_name_ext
        all_scenarios = json.loads(string)["scenarios"]

        fixed_scenarios = {}
        fixed_scenarios["scenarios"] = []

        for scenario in all_scenarios:
            if "args" in scenario["params"]:
                scenario["params"] = change_param_format(scenario["params"]["args"]["new_params"])
                fixed_scenarios["scenarios"].append(scenario)
            else:
                fixed_scenarios["scenarios"].append(scenario)

        with open(fixed_scenario, "a+") as fixed_scenarios_file:
                fixed_scenarios_file.writelines(json.dumps(fixed_scenarios, indent=4))



            
                
            
