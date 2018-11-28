#!/bin/bash
cd ~/ci/beos-core/$CI_COMMIT_REF_NAME/build
echo "Starting integration tests"
if ! make test
then
  printf "Test failure. Exiting..."
  exit 1
fi

echo "Starting unit tests"

if ! ./unittests/unit_test --log_level=test_suite
then
  printf "Unit test failure. Exiting..."
  exit 2
fi

