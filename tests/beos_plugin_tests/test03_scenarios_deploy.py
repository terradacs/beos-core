#!/usr/bin/env python3

import os
import sys
import glob
import argparse
import datetime
import subprocess


sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/beos_test_utils")
from summarizer import Summarizer
from cmdlineparser import parser


test_args = []

def check_subdirs(_dir):
  error = False
  tests = sorted(glob.glob(_dir+"/*.py"))
  if tests:
    for test in tests:
      root_error = run_script(test)
      if root_error:
        error = root_error
  return error


def write_error_to_summary_file_if_not_exists(test_file, _error_file):
    with open(_error_file, "r") as err:
      if os.stat(_error_file).st_size:
        path = os.path.dirname(test_file)
        if not os.path.exists(path+"/summary"):
          os.mkdir(path+"/summary")
        data = os.path.split(test_file)
        cdir = data[0] if data[0] else "."
        cfile = data[1]
        summary = Summarizer(cdir+"/"+cfile)
        summary.equal(False, True, "Unhandeled exception occured {0}".format(err.read()))
        summary.summarize()

def run_script(_test, _multiplier = 1, _interpreter = None ):
  error = True
  error_file = _test+"_error"
  try:
    with open(error_file, "w") as err:
      interpreter = _interpreter if _interpreter else "python3"
      ret_code = subprocess.call(interpreter + " " + _test + " " + test_args, shell=True, stderr=err)
    if ret_code == 0:
      error = False
    else:
      write_error_to_summary_file_if_not_exists(_test, error_file)
      error = True
  except Exception as _ex:
    print("Exception occures in run_script `{0}`".format(str(_ex)))
    error = True
  finally:
    if os.path.exists(error_file):
      os.remove(error_file)
    return error

if __name__ == "__main__":
  args = parser.parse_args()
  for key, val in args.__dict__.items():
    if val :
      test_args.append("--"+key.replace("_","-")+ " ")
      test_args.append(val)
  test_args = " ".join(test_args)
  try:
    error = True
    if os.path.isfile(args.scenarios):
      error = run_script(args.scenarios)
    elif os.path.isdir(args.scenarios):
      error = check_subdirs(args.scenarios)

  except Exception as _ex:
    print("Exception occured `{0}`.".format(str(_ex)))
    error = True
    
  if error:
    exit(1)
  else:
    exit(0)
