#!/bin/bash
cd ~/ci/build/$CI_COMMIT_REF_NAME
echo "Starting integration tests"
make test
echo "Starting unit tests"
./unittests/unit_test --log_level=test_suite