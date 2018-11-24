#!/bin/bash
cd ~/ci/build/$CI_COMMIT_REF_NAME
echo "Starting integration tests"
if ! make test
  printf "Test failure. Exiting..."
  exit 1
fi

echo "Starting unit tests"

if ! ./unittests/unit_test --log_level=test_suite
  printf "Unit test failure. Exiting..."
  exit 2
fi

