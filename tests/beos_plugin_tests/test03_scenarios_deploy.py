#!/usr/bin/env python3

import os
import sys
import glob
import argparse
import datetime
import subprocess


sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/beos_test_utils")
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


def run_script(_test, _multiplier = 1, _interpreter = None ):
  try:
    interpreter = _interpreter if _interpreter else "python3"
    ret_code = subprocess.call(interpreter + " " + _test + " " + test_args, shell=True)
    if ret_code == 0:
      return False
    else:
      return True
  except Exception as _ex:
    print("Exception occures in run_script `{0}`".format(str(_ex)))
    return True


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
