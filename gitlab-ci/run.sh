#!/bin/bash
cd ~/ci/beos-core/$CI_ENVIRONMENT_SLUG/$CI_COMMIT_REF_NAME/build
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