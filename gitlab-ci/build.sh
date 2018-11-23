#!/bin/bash
rm -rf ~/ci/build/$CI_COMMIT_REF_NAME
which ssh-agent || ( apt-get update -y && apt-get install openssh-client -y )
eval $(ssh-agent -s)
ssh-add <(echo "$SSH_PRIVATE_KEY")
git submodule update --init --recursive
cd cd-scripts
cp config-$CI_BEOS_CONFIG_NAME.py config.py
./deploy.py --build-beos
cat beos_deploy_main.log
echo "Removing object files"
find ~/ci/build/$CI_COMMIT_REF_NAME -type f -name '*.o' -delete
echo "Stopping old keosd instance"
kill -2 $(lsof -t -i:8900) || true
python3 ./wait.py $(lsof -t -i:8900)
echo "Stopping old nodeos instance"
kill -2 $(lsof -t -i:8888) || true
python3 ./wait.py $(lsof -t -i:8888)
./deploy.py --initialize-beos
cat beos_deploy_main.log