import os
# logging
LOG_FORMAT = '%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
from logging import INFO, DEBUG, ERROR, WARNING, CRITICAL
LOG_LEVEL = INFO

# directory where all sources will be downloaded
SOURCES_DOWNLOAD_DIR = os.environ["HOME"] + "/beos-build"
# beos main directory
BEOS_DIR = SOURCES_DOWNLOAD_DIR + "/beos-core"
EOSIO_SRC_DIR = BEOS_DIR
# beos build directory - only for running initial cmake
# main cmake will be called from EOSIO build directory
BEOS_BUILD_DIR = BEOS_DIR + "/build"
EOSIO_BUILD_DIR = BEOS_BUILD_DIR
# path to beos sources repository
BEOS_REPOSITORY_PATH = "git@gitlab.syncad.com:blocktrades/beos.git"
BEOS_REPOSITORY_BRANCH = 'beos-initial-release'
#

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
#BOOST_INSTALL_DIR = BOOST_INSTALL_PREFIX + "/include/boost"
BOOST_INSTALL_DIR = "/home/syncad/beos-build/boost-allcpu/boost-prebuild-1.67"

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
EOSIO_INSTALL_PREFIX = BEOS_BUILD_DIR + "/eosio"
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
COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY = "EOS6F1uhwi7nPcon3hm2bJuyrp79JbqLqLkK9muhdYedowHQsBGw7"
COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY = "EOS6F1uhwi7nPcon3hm2bJuyrp79JbqLqLkK9muhdYedowHQsBGw7"

COMMON_SYSTEM_ACCOUNT_OWNER_PRIVATE_KEY = "5J5NNoRAVdKpQ2Hs4TyVEJiHjYsSptQwwBTRPYMPEE8mE7aaxEX"
COMMON_SYSTEM_ACCOUNT_ACTIVE_PRIVATE_KEY = "5J5NNoRAVdKpQ2Hs4TyVEJiHjYsSptQwwBTRPYMPEE8mE7aaxEX"


# path to contracts directory
CONTRACTS_DIR = BEOS_BUILD_DIR + "/contracts/"

#Wallet password: PW5JAPaRBe7Y8ToUYcC5dRowjBAvx7q2cGuzz6vwh6qdW2dBmW3D

# The main keys to the blockchain net, that allow creation of system accounts
# EOSIO public key
EOSIO_PUBLIC_KEY = "EOS7BSs5hWnEMxxoVRNgAwT1qz57PPoBV2jacZE3VhEEz1xdeVTZd"
# KEEPING KEYS IN PUBLIC FILE IS NOT WISE!
# EOSIO private key
EOSIO_PRIVATE_KEY = "5KPR3ETzJwAxtLNFjxj3SbLMy8BCCZKNP484FhiYyDWDjoAJG8L"

# Keys for `beos.gateway`
BEOS_GATEWAY_PUBLIC_KEY = "EOS4xmjieGzyf3Qrh1bw2PJBHLeNj7BGAQF5Y3DWeDugFFNxzSvhU"
BEOS_GATEWAY_PRIVATE_KEY = "5KepMSYjvo5Nb46qNLsszmtS7d3LoaYa77vrEEwKmLcs4icDGZU"

# Keys for `beos.distrib`
BEOS_DISTRIB_PUBLIC_KEY = "EOS5w5ukedWyMnXhTMv6tW4Ey96TdqAn7KAFMxgW8fi3n4qgkRYzi"
BEOS_DISTRIB_PRIVATE_KEY = "5KWoxNppdkJHg4N8UnUmLbrd5TYgvyDJ3tfMCZD4Mx9Jh9ZQXBk"

# path to keosd executable
KEOSD_EXECUTABLE = BEOS_BUILD_DIR + "/programs/keosd/keosd"
# keosd ip address
KEOSD_IP_ADDRESS = "127.0.0.1"
# keosd port
KEOSD_PORT = 8902
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
NODEOS_PORT = 8882
# nodeos certificate chain file - mandatory for https
NODEOS_CERTIFICATE_CHAIN_FILE = None
# nodeos private key file path - mandatory for https
NODEOS_PRIVATE_KEY_FILE = None
# direcotry with nodes data
NODEOS_WORKING_DIR = os.environ["HOME"] + "/beos-build/beos.node"
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
    COMMON_SYSTEM_ACCOUNT_ACTIVE_PRIVATE_KEY
]
# source file for beos config
BEOS_CONFIG_FILE_SRC = os.path.dirname(os.path.abspath(__file__)) + "/resources/beos.config.ini"
# beos config file name
BEOS_CONFIG_FILE = "beos.config.ini"
# source file for genesis file
GENESIS_JSON_FILE_SRC = os.path.dirname(os.path.abspath(__file__)) + "/resources/genesis.json"
# genesis json file name
GENESIS_JSON_FILE = "genesis.json"
#starting node index
START_NODE_INDEX = 0

##############      configuration data for contracts/accounts     ###############
#################################################################################
PROXY_ASSET_NAME = "PXBTS"
PROXY_ASSET_PRECISION = 4 # 10^4
# maximum amount that will ever be allowed to be issued (must cover all BTS)
PROXY_TOTAL_SUPPLY = "10000000000.0000" # as string to preserve zeros (they establish precision)

CORE_SYMBOL_PRECISION = 4 # 10^4
# maximum amount that will ever be allowed to be issued (includes "perpetual" inflation)
CORE_TOTAL_SUPPLY = "10000000000.0000" # as string to preserve zeros (they establish precision)

# 2724*2 (doubled minimal amount) * 30000 (number of accounts to create before ram has to be refilled) + gateway own needs, all rounded up
GATEWAY_INIT_RAM = "164000000"
GATEWAY_INIT_NET = "10000.0000" # just for gateway needs
GATEWAY_INIT_CPU = "10000.0000" # just for gateway needs

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

# reward_pool = ((end-start)/interval + 1) * reward_per_interval
# beos.distrib needs enough to cover all rewards, plus some for its own needs
DISTRIB_INIT_RAM = "32765010000" # (280-7)*24 + 1 intervals * 5000000 per interval plus some 10000 for itself
DISTRIB_INIT_NET = "1758000.0000" # (98-7)*24 + 1 intervals * (800/2 (users) + 800/2 (trustee)) per interval plus some 10000 for itself
DISTRIB_INIT_CPU = "1758000.0000" # as above

# sum of BEOS needed to cover gateway and distrib initial resources; note that the more we issue the more expensive ram will be, which means
# we must issue even more; we are trying to buy half of all available ram after all
CORE_INITIAL_SUPPLY = 3_674_470_000 * (10 ** CORE_SYMBOL_PRECISION)
MIN_ACTIVATED_STAKE_PERCENT = 15

### init loggers
global log_main
log_main = open(MAIN_LOG_PATH, "a+")
global log_error
log_error = open(ERROR_LOG_PATH, "a+")
