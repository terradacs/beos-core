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

def omit_dir(_dir):
  print(_dir)
  if "beos_test_utils" in _dir or \
     "cd_scripts" in _dir:
    return True
  else:
    return False

def check_subdirs(_dir):
  error = False
  for root, subdirs, _ in os.walk(_dir):
    if omit_dir(root):
      continue
    tests = sorted(glob.glob(root+"/*.py"))
    for test in tests:
      root_error = run_script(test)
      if root_error:
        error = root_error
    for subdir in subdirs:
      if omit_dir(subdir):
        continue
      sub_error = check_subdirs(subdir)
      if sub_error:
        error = sub_error
  return error


def run_script(_test, _multiplier = 1, _interpreter = None ):
  try:
    interpreter = _interpreter if _interpreter else "python3"
    actual_args = test_args.split()
    for index, arg in enumerate(actual_args) :
      if arg == "--scenario-multiplier":
        actual_args[index+1] = str(_multiplier)
    actual_args = " ".join(actual_args)
    ret_code = subprocess.call(interpreter + " " + _test + " " + actual_args, shell=True)
    if ret_code == 0:
      return False
    else:
      return True
  except Exception as _ex:
    print("Exception {0}".format(str(_ex)))
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
      if error:
        error = error
    elif os.path.isdir(args.scenarios):
      error = check_subdirs(args.scenarios)

  except Exception as _ex:
    error = True
    
  if error:
    exit(1)
  else:
    exit(0)
