#!/bin/bash
cd ~/ci/build/$CI_COMMIT_REF_NAME
echo "Starting keosd and nodeos"
if ! python3 ./run.py
then
  printf "Unable to start BEOS instance"
  exit 1
fi

echo "Started keosd instance:"
echo "Started keosd instance (should be empty):"
lsof -t -i:8900 || true
echo "Started nodeos instance:"
echo "Started nodeos instance (should be empty):"
lsof -t -i:8888 || true
screen -list || true