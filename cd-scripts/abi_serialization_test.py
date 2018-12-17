#!/usr/bin/env python3

import abi_def
import json

if __name__ == "__main__":
  import sys
  import os

  if len(sys.argv) != 2:
    print("Usage: {0} path_to_abi.abi".format(sys.argv[0]))
    sys.exit(0)

  try:
    path = os.path.normpath(sys.argv[1])
    with open(path, "r") as abi_file:
      print("Reading file: {0}".format(path))
      abi_as_json = json.loads(abi_file.read())
      print("ABI file as text:")
      print(abi_as_json)
      abi_def_ob = abi_def.Abi(abi_as_json)
      print("ABI file as dict:")
      print(abi_def_ob.to_dict())
      print("ABI file serialized:")
      print(abi_def_ob.pack().hex())
  except Exception as ex:
    print("Exception during test: {0}".format(ex))
    sys.exit(1)


