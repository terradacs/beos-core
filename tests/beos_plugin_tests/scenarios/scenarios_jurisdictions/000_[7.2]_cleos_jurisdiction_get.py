#!/usr/bin/python3

import os
import sys
import time
import datetime
import requests

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import init, ActionResult, ResourceResult, VotersResult


def names(aDistance):
    name_result = ""
    for i in range(3):
        name_result += chr(97 + aDistance)

    return name_result


def lotsOfRecords(amount):
    to_return = ''
    for i in range(amount):
        to_return += '{ "new_code": ' + str(i) + ', "new_name": "sampleName' + str(
            i) + '", "new_description": "sampleDescription' + str(i) + '"}'
        if i + 1 != amount:
            to_return += ', '

    return to_return


def long_names(length : int, word : str = "x"):
    return word*length

def generate_names_array(amount):
    counter = 100000
    to_return = []
    for i in range(amount):
        to_return.append("a" + str(counter))
        counter += 1
    return '\"'+"\", \"".join(to_return)+"\""


if __name__ == "__main__":
    try:
        node, summary, args, log = init(__file__)
        producers = node.create_producers(2, "1000.0000 BTS")
        node.run_node()
        newparams = {
            "beos": {
                "starting_block": 10,
                "next_block": 0,
                "ending_block": 20,
                "block_interval": 10,
                "trustee_reward": 1000000
            },
            "ram": {
                "starting_block": 10,
                "next_block": 0,
                "ending_block": 20,
                "block_interval": 10,
                "trustee_reward": 0
            },
            "proxy_assets": ["0.0000 BTS"],
            "ram_leftover": 300000,
            "starting_block_for_initial_witness_election": 10
        }

        node.changeparams(newparams)
        node.wait_till_block(25)

		# Checking is there no jurisdictions
        rpc = node.get_url_caller()
        response = rpc.chain.get_table_rows({"scope": "eosio", "code": "eosio", "table": "infojurisdic", "json": True})
        log.info("response {}".format(response))
        summary.equal(True, len(response["rows"]) == 0, "There should be no jurisdictions.")

        # PREPARING

        node.make_cleos_call(
            ["push", "action", "eosio", "addjurisdict", '[ "eosio", 1, "Wakanda", "country1" ]', "-p", "eosio"])
        node.make_cleos_call(
            ["push", "action", "eosio", "addjurisdict", '[ "eosio", 2, "Asgard", "country2" ]', "-p", "eosio"])
        node.make_cleos_call(
            ["push", "action", "eosio", "addjurisdict", '[ "eosio", 3, "Hala", "country3" ]', "-p", "eosio"])

        resINT, resSTR = node.make_cleos_call(["push", "action", "eosio", "updateprod",
                                               '{ "data": { "producer": "eosio", "jurisdictions": [1,2]}}', "-p",
                                               "eosio"])

        # get producer_jurisdiction
        resINT, resSTR = node.make_cleos_call(["get", "producer_jurisdiction", '[ {} ]'.format(generate_names_array(3000))])
        summary.equal(True, str(resSTR).find("Query size is greater than query limit") != -1, "there should be error")
        summary.equal(True, resINT != 0, "this querry should crash")

        resINT, resSTR = node.make_cleos_call(["get", "producer_jurisdiction", '[ "{}" ]'.format(long_names(2000))])
        summary.equal(True, str(resSTR).find("Invalid name") != -1, "there should be error")
        summary.equal(True, resINT != 0, "this querry should crash")

        resINT, resSTR = node.make_cleos_call([ "get", "producer_jurisdiction", "1"])
        summary.equal(True, str(resSTR).find("Bad Cast") != -1, "there should be error")
        summary.equal(True, resINT != 0, "this querry should crash")

        # get all_producer_jurisdiction_for_block
        resINT, resSTR = node.make_cleos_call(["get", "all_producer_jurisdiction_for_block", long_names(10, "9999") ])
        summary.equal(True, str(resSTR).find("std::out_of_range") != -1, "there should be error")
        summary.equal(True, resINT != 0, "this querry should crash")

        # get producer_jurisdiction_for_block
        resINT, resSTR = node.make_cleos_call(["get", "producer_jurisdiction_for_block", "eosio", "eosio"])
        summary.equal(True, str(resSTR).find("std::invalid_argument") != -1, "there should be error")
        summary.equal(True, resINT != 0, "this querry should crash")

        resINT, resSTR = node.make_cleos_call(["get", "producer_jurisdiction_for_block", "eosio", long_names(10, "9999") ])
        summary.equal(True, str(resSTR).find("std::out_of_range") != -1, "there should be error")
        summary.equal(True, resINT != 0, "this querry should crash")

        # get producer_jurisdiction_history
        resINT, resSTR = node.make_cleos_call(["get", "producer_jurisdiction_history", "eosio", "fafwadf", "wfafwafw"])
        summary.equal(True, str(resSTR).find("bad lexical cast") != -1, "there should be error")
        summary.equal(True, resINT != 0, "this querry should crash")

    except Exception as _ex:
        log.exception("Exception `{0}` occures while executing `{1}` tests.".format(str(_ex), __file__))
        summary.equal(False, True, "Exception occured durring testing.")

    finally:
        summary_status = summary.summarize()
        node.stop_node()
        exit(summary_status)
