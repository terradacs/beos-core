import os
# logging
LOG_FORMAT = '%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
from logging import INFO, DEBUG, ERROR, WARNING, CRITICAL
LOG_LEVEL = INFO

# directory where all sources will be downloaded
SOURCES_DOWNLOAD_DIR = os.environ["HOME"] + "/Sources"
# beos main directory
BEOS_DIR = SOURCES_DOWNLOAD_DIR + "/beos-core"
# path to beos sources repository
#BEOS_REPOSITORY_PATH = "git@gitlab.syncad.com:blocktrades/beos-core.git"
BEOS_REPOSITORY_PATH = "https://gitlab.syncad.com/blocktrades/beos-core.git" 

BEOS_REPOSITORY_BRANCH = 'beos-initial-release'
#
# eosio build directory - here will land final build
BEOS_BUILD_DIR = os.environ["HOME"] + "/Builds/build/"

MAIN_LOG_PATH = os.path.dirname(os.path.abspath(__file__)) + "/beos_deploy_main.log"
ERROR_LOG_PATH = os.path.dirname(os.path.abspath(__file__)) + "/beos_deploy_main.log"

#######################        Default compiler           #######################
#################################################################################
DEFAULT_C_COMPILER = "/usr/bin/clang-4.0"
DEFAULT_CXX_COMPILER = "/usr/bin/clang++-4.0"

####################### Custom libraries build parameters #######################
#################################################################################
# default install prefix for custom libraries (sudo needed)
DEFAULT_INSTALL_PREFIX = "/usr/local"

# parameters for boost custom instalation
BOOST_INSTALL_PREFIX = DEFAULT_INSTALL_PREFIX
BOOST_INSTALL_DIR = BOOST_INSTALL_PREFIX + "/include/boost"

# parameters for MognoDB C driver
MONGO_C_INSTALL_PREFIX = DEFAULT_INSTALL_PREFIX
MONGO_C_INSTALL_DIR = MONGO_C_INSTALL_PREFIX + "/include/libmongoc-1.0"

# parameters for MognoDB C++ driver
MONGO_CXX_INSTALL_PREFIX = DEFAULT_INSTALL_PREFIX
MONGO_CXX_INSTALL_DIR = MONGO_CXX_INSTALL_PREFIX + "/include/mongocxx"

# parameters for secp256k1 library installation
SECP256_INSTALL_PREFIX = DEFAULT_INSTALL_PREFIX

# parameters for WASM compiler installation
WASM_INSTALL_PREFIX = DEFAULT_INSTALL_PREFIX
WASM_INSTALL_DIR = WASM_INSTALL_PREFIX + "/wasm"

#######################       EOSIO build parameters      #######################
#################################################################################
# install prefix for EOSIO installation
EOSIO_INSTALL_PREFIX = DEFAULT_INSTALL_PREFIX + "/eosio"
# build type
EOSIO_BUILD_TYPE = "Release"
# coverage testing switch
ENABLE_COVERAGE_TESTING = "false"
#
BUILD_MONGO_DB_PLUGIN = "false"
#
DOXYGEN = "false"
# core symbol name
CORE_SYMBOL_NAME = "BEOS"
# path to openssl
OPENSSL_ROOT_DIR = "/usr/include/openssl"

#######################       EOSIO config parameters     #######################
#################################################################################
# When account is created, its public keys (owner & active) are set. The keys below are given to all system accounts, i.e.
# eosio.msig, eosio.names, eosio.saving, eosio.bpay, eosio.vpay, eosio.unregd, eosio.ram, eosio.ramfee,
# eosio.token, eosio.stake, beos.token, beos.init, beos.market
COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY = "EOS6AAWx6uvqu5LMBt8vCNYXcxjrGmd3WvffxkBM4Uozs4e1dgBF3"
COMMON_SYSTEM_ACCOUNT_OWNER_PRIVATE_KEY = "5JpSDcXq6TfzQxkFmYFXQygHR6jG3pWjtGnRmtHQd7YmCxoqLtU"

COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY = "EOS53QRGWCMxxHtKqFjiMQo8isf3so1dUSMhPezceFBknF8T5ht9b"
COMMON_SYSTEM_ACCOUNT_ACTIVE_PRIVATE_KEY = "5Hw8qBPp4Hpbf2wja6bA34t3x58cp4XBmDxkz7HKQGsFZ4vJ2HT"
# path to contracts directory
CONTRACTS_DIR = BEOS_BUILD_DIR + "/contracts/"

# The main keys to the blockchain net, that allow creation of system accounts
# EOSIO public key
EOSIO_PUBLIC_KEY = "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
# KEEPING KEYS IN PUBLIC FILE IS NOT WISE!
# EOSIO private key
EOSIO_PRIVATE_KEY = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"

# Keys for `beos.gateway`
BEOS_GATEWAY_PUBLIC_KEY = "EOS6Y1LJCZC1Mrp9EoLcmkobJHoNnVQMqLcNAxU5xL5iXwqzctjmd"
BEOS_GATEWAY_PRIVATE_KEY = "5Ka14byMGwBqE4Q149pffSjXf547otfZ1NKdTEq1ivwg9DjMoi6"

# Keys for `beos.distrib`
BEOS_DISTRIB_PUBLIC_KEY = "EOS5FUjQDE6QLiGZKt7hGwBypCAJPL53X3SYf6Gf4JxMkdyH1wMrF"
BEOS_DISTRIB_PRIVATE_KEY = "5HvT4NQKyLMojJpa2qPCquwkGmppC6dqCJQK7cBcMFPR2i3Ei4p"

#Keys for beos.trustee
TRUSTEE_OWNER_PUBLIC_KEY = "EOS5X4pqjE68BCu4qexP66xLNtTzVvGHjQmgQ9zsjLG6husPwN81G"
TRUSTEE_OWNER_PRIVATE_KEY = "5JivSPSm7QRsvf7DZ1mMdYRgmagfGGs3xNTRtALwR2PXc7LMMri"

TRUSTEE_ACTIVE_PUBLIC_KEY = "EOS591VeMZCaZP5eXKv4TvyEXetFUyM2veA7hxKkFteJc62VUikmn"
TRUSTEE_ACTIVE_PRIVATE_KEY = "5JUqt5QsguMa1emcQuV6UvwYQHN89uXqeYqtt2dMkp2hzwGyCR6"

#keys for producerjson
PRODUCERJSON_OWNER_PUBLIC_KEY = "EOS4tg1DaJ1dJZmBsHbCr51LeELV8sG4cAnfvGzepAYo4FU2oCK4q"
PRODUCERJSON_OWNER_PRIVATE_KEY = "5JAz4TPNYNRMjFUT8qUR4aVeRcH2yKjqq226kdYP1JFy6JcTCyo"

PRODUCERJSON_ACTIVE_PUBLIC_KEY = "EOS5vVpk9yzKCAfWrwBJg2sFYQUKd1KwaHEYPeXamXYYgu3beSNX6"
PRODUCERJSON_ACTIVE_PRIVATE_KEY = "5HwY1gxzGmiVoFmTz6oKfzpnS4t2pc44eArezvMZLFaoGQJURBP"

#keys for regproxyinfo
REGPROXYINFO_OWNER_PUBLIC_KEY = "EOS5LjSbxg5AXmW7tkfQ9cWKoXa1tJCGdgA8t4WeCTHdZuASPAFpz"
REGPROXYINFO_OWNER_PRIVATE_KEY = "5KYU6rcMyKWcnDT17Mm4RyhmHJgtYvC62ywekKNjCK94WGPyhuV"

REGPROXYINFO_ACTIVE_PUBLIC_KEY = "EOS4uM4sYPWrjWt3aeLiQ6yBFsxBYJLvuTrdNAQhPhPmCB9B31Xi3"
REGPROXYINFO_ACTIVE_PRIVATE_KEY = "5KeanX7RooeHb8goe1ghirt74R1GGqYZtsyKfqszEUGrDeGGGPt"

# path to keosd executable
KEOSD_EXECUTABLE = BEOS_BUILD_DIR + "/programs/keosd/keosd"
# keosd ip address
KEOSD_IP_ADDRESS = "127.0.0.1"
# keosd port
KEOSD_PORT = 8900
# keosd certificate chain file - mandatory for https
KEOSD_CERTIFICATE_CHAIN_FILE = None
# keosd private key file path - mandatory for https
KEOSD_PRIVATE_KEY_FILE = None

# path to cleos executable
CLEOS_EXECUTABLE = BEOS_BUILD_DIR + "/programs/cleos/cleos"
# path to nodeos executable
NODEOS_EXECUTABLE = BEOS_BUILD_DIR + "/programs/nodeos/nodeos"
# nodeos ip address
NODEOS_IP_ADDRESS = "127.0.0.1"
# nodeos port
NODEOS_PORT = 8888
# nodeos certificate chain file - mandatory for https
NODEOS_CERTIFICATE_CHAIN_FILE = None
# nodeos private key file path - mandatory for https
NODEOS_PRIVATE_KEY_FILE = None
# direcotry with nodes data
NODEOS_WORKING_DIR = os.environ["HOME"] + "/beos-data/"
# directory in which wallet files are held
DEFAULT_WALLET_DIR = os.environ["HOME"] + "/eosio-wallet"
# name of the master wallet
MASTER_WALLET_NAME = "beos_master_wallet"
# directory with password file for master wallet
WALLET_PASSWORD_DIR = BEOS_BUILD_DIR + "/wallet/"
# password file for master wallet KEEP SECURE
WALLET_PASSWORD_PATH = WALLET_PASSWORD_DIR + "wallet.dat"
# KEEPING KEYS IN PUBLIC FILE IS NOT WISE!
# if you are creating system accounts with diferent keys the keys should be imported to
# wallet, add them here. 
SYSTEM_ACCOUNT_KEYS = [
    EOSIO_PRIVATE_KEY,
    BEOS_GATEWAY_PRIVATE_KEY,
    BEOS_DISTRIB_PRIVATE_KEY,
    COMMON_SYSTEM_ACCOUNT_OWNER_PRIVATE_KEY,
    COMMON_SYSTEM_ACCOUNT_ACTIVE_PRIVATE_KEY,
    TRUSTEE_OWNER_PRIVATE_KEY,
    TRUSTEE_ACTIVE_PRIVATE_KEY,
    PRODUCERJSON_OWNER_PRIVATE_KEY,
    PRODUCERJSON_ACTIVE_PRIVATE_KEY,
    REGPROXYINFO_OWNER_PRIVATE_KEY
]
# source file for beos config
BEOS_CONFIG_FILE_SRC = BEOS_BUILD_DIR + "/resources/config.ini"
# beos config file name
BEOS_CONFIG_FILE = "config.ini"
# source file for genesis file
GENESIS_JSON_FILE_SRC = BEOS_BUILD_DIR + "/resources/genesis.json"
# genesis json file name
GENESIS_JSON_FILE = "genesis.json"
#starting node index
START_NODE_INDEX = 0

PRODUCER_NAME = "eosio"

##############              Cmake tests configuration             ###############
#################################################################################
DISABLE_FAILING_TESTS = "true"
DISABLE_WASM_TESTS = "true"

##############      configuration data for contracts/accounts     ###############
#################################################################################
PROXY_ASSET_NAME = "PXBTS"
PROXY_ASSET_PRECISION = 4 # 10^4
# maximum amount that will ever be allowed to be issued (must cover all BTS)
PROXY_TOTAL_SUPPLY = "10000000000.0000" # as string to preserve zeros (they establish precision)

CORE_SYMBOL_PRECISION = 4 # 10^4
# maximum amount that will ever be allowed to be issued (includes "perpetual" inflation)
CORE_TOTAL_SUPPLY = "10000000000.0000" # as string to preserve zeros (they establish precision)
CORE_INITIAL_SUPPLY = 3674470000 * (10 ** CORE_SYMBOL_PRECISION) # equals total supply of BTS
MIN_ACTIVATED_STAKE_PERCENT = 15

# 2724*2 (doubled minimal amount) * 30000 (number of accounts to create before ram has to be refilled) + gateway own needs, all rounded up
GATEWAY_INIT_RAM = 164000000
GATEWAY_INIT_NET = 10000 * (10**CORE_SYMBOL_PRECISION) # just for gateway needs
GATEWAY_INIT_CPU = 10000 * (10**CORE_SYMBOL_PRECISION) # just for gateway needs
# beos.distrib needs enough to cover all rewards, plus some for its own needs; net/cpu are calculated from other params
DISTRIB_INIT_RAM = 32000300000

STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION = 100
STARTING_BLOCK_FOR_BEOS_DISTRIBUTION = 7 * 24 * 3600 * 2 # days(7).to_seconds() * 2
ENDING_BLOCK_FOR_BEOS_DISTRIBUTION = 98 * 24 * 3600 * 2 # days(98).to_seconds() * 2
DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_BEOS_DISTRIBUTION = 1 * 3600 * 2 # hours(1).to_seconds() * 2
AMOUNT_OF_REWARD_BEOS = 800 * CORE_SYMBOL_PRECISION # 800 * asset().symbol.precision()
STARTING_BLOCK_FOR_RAM_DISTRIBUTION = 7 * 24 * 3600 * 2 # days(7).to_seconds() * 2
ENDING_BLOCK_FOR_RAM_DISTRIBUTION = 280 * 24 * 3600 * 2 # days(280).to_seconds() * 2
DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_RAM_DISTRIBUTION = 1 * 3600 * 2 # hours(1).to_seconds() * 2
AMOUNT_OF_REWARD_RAM = 5000000 # 5000000 is a number not asset
STARTING_BLOCK_FOR_TRUSTEE_DISTRIBUTION = 7 * 24 * 3600 * 2 # days(7).to_seconds() * 2 [UNUSED]
ENDING_BLOCK_FOR_TRUSTEE_DISTRIBUTION = 98 * 24 * 3600 * 2 # days(98).to_seconds() * 2 [UNUSED]
DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_TRUSTEE_DISTRIBUTION = 1 * 3600 * 2 # hours(1).to_seconds() * 2 [UNUSED]
AMOUNT_OF_REWARD_TRUSTEE = 800 * CORE_SYMBOL_PRECISION # 800 * asset().symbol.precision()

### init loggers
global log_main
log_main = open(MAIN_LOG_PATH, "a+")
global log_error
log_error = open(ERROR_LOG_PATH, "a+")
