import os
# logging
LOG_FORMAT = '%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
from logging import INFO, DEBUG, ERROR, WARNING, CRITICAL
LOG_LEVEL = INFO

# directory where all sources will be downloaded
SOURCES_DOWNLOAD_DIR = os.environ["HOME"] + "/beos-build"
# beos main directory
BEOS_DIR = SOURCES_DOWNLOAD_DIR + "/beos-core"
# beos build directory - only for running initial cmake
# main cmake will be called from EOSIO build directory
BEOS_BUILD_DIR = BEOS_DIR + "/build/LDebug"
EOSIO_BUILD_DIR = BEOS_BUILD_DIR
# path to beos sources repository
BEOS_REPOSITORY_PATH = "git@gitlab.syncad.com:blocktrades/beos-core.git"
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
EOSIO_BUILD_TYPE = "Debug"
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

#Wallet password: PW5JAPaRBe7Y8ToUYcC5dRowjBAvx7q2cGuzz6vwh6qdW2dBmW3D

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
TRUSTEE_OWNER_PUBLIC_KEY = "EOS7WSRAFdYGcNQ6YWp2bA1Sjba8dXbf6kVbYxMkzvdF92StS2kxS"
TRUSTEE_OWNER_PRIVATE_KEY = "5KAwbXnWrtMFrzJZd9bKPicdRtGhfd5cDdJCXmkPeUcnLDjYac6"

TRUSTEE_ACTIVE_PUBLIC_KEY = "EOS5GcfU61Nq3YmdxxFoLo1eY9Rx6SYkwNp7n9dit1rVzJBxo6BHT"
TRUSTEE_ACTIVE_PRIVATE_KEY = "5JoXJePQqe1NACbPYVickFkUvJtx6kf8j1e1v81Ei9XyMB7pNb3"

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
KEOSD_IP_ADDRESS = "0.0.0.0"
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
NODEOS_IP_ADDRESS = "0.0.0.0"
# nodeos port
NODEOS_PORT = 8888
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
    COMMON_SYSTEM_ACCOUNT_OWNER_PRIVATE_KEY,
    COMMON_SYSTEM_ACCOUNT_ACTIVE_PRIVATE_KEY,
    TRUSTEE_OWNER_PRIVATE_KEY,
    TRUSTEE_ACTIVE_PRIVATE_KEY,
    PRODUCERJSON_OWNER_PRIVATE_KEY,
    PRODUCERJSON_ACTIVE_PRIVATE_KEY,
    REGPROXYINFO_OWNER_PRIVATE_KEY,
    REGPROXYINFO_ACTIVE_PRIVATE_KEY
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

PRODUCERS_ARRAY = {
    "beos.proda":
    {
        "pub_active" : "EOS76sgTLYbsKKkZSmbSeSYdRLzycKvZhW3dTfbRkBuJC4hcGiFsw",
        "prv_active" : "5HzpPRKXqMszfouNzVpUmxGWhyDUkFXpVxxYpMz1G3VocmHhCzA",
        "pub_owner" : "EOS7mRtT2Wop2G8rV5Vhww9dpqTFTetJbhTiryPa4uJaJ2Weybhw5",
        "prv_owner" : "5J8ReH3N2K139758DKKYEqnE44vDuXTW3fVKSnWQQfdCt3xVWsY",
        "url" : "https://producerooo1.html"
    },
    "beos.prodb":
    {
        "pub_active" : "EOS6nYVtMwQnvxmFSRw9jxm2poG5nL1czMunXqi6RRxFdTonyJQdH",
        "prv_active" : "5JR2QvDqW2NzqNRvxYUcf9erVYTYgLXe1kkw19D8YBwcoMAbtuF",
        "pub_owner" : "EOS86GbqxJxiGwHDAg3EXf7GvXgDw9aDp7XMKpNHTGZZH8ZY7vucy",
        "prv_owner" : "5JwtX6BqD2xN18Vv6tZnCTmRUL7dvwqTdXH1VEbNRU2qH87m9Ai",
        "url" : "https://producerooo1.html"
    },
    "beos.prodc":
    {
        "pub_active" : "EOS7J8Pr7GK7pJxrfbcrw3h8EagX6sYk3fUuBMhy1oGApBZwAdfhH",
        "prv_active" : "5JYyHdphb1Y8QeH4ktBBxpXWM5dYUgXUxwPD6ExRR9tSeMqry5q",
        "pub_owner" : "EOS5eKMP3D3wrWoDkGQSx6rFfZLQyHdVjDQ5Pg3yEPqP9tKQb1Beu",
        "prv_owner" : "5HzXknFdCjpkJKvdZe2r5zuEf6TajUXowqcC9gcHfVQQ6WzPJgN",
        "url" : "https://producerooo1.html"
    },
    "beos.prodd":
    {
        "pub_active" : "EOS5DCrWB7vNd9juJyGLwTNJWcVW9uEXzDWhhi9EG5GSYALJJ6q3t",
        "prv_active" : "5JGiznRbzofsGJegENLNqvRiAXbJ2FhYEkT8inkaQidVH5JM63S",
        "pub_owner" : "EOS5tt5ssvrJpQ5MiRHQDz8oM5JHDmwn4zFdUBup6mTQU3cccQjdL",
        "prv_owner" : "5JWKthYbzmF6epr4MRjkgkdBsSJcGKiPDYkPT3AzGvgYiLce3WN",
        "url" : "https://producerooo1.html"
    },
    "beos.prode":
    {
        "pub_active" : "EOS8garBR6Ny2R6UUpK9w61pbiyLEhQDGBoqAFU4TcWipEBjYEELN",
        "prv_active" : "5JWCsSbS6bFzw9GWSpDzkb2p251EPkFe4Cq2ZaU2hAhnkxiiWGk",
        "pub_owner" : "EOS4uwvUuUc9ZEqz6AAhDnz93k6jDb8XWUoby4qRnNXVmyLWuQK1o",
        "prv_owner" : "5JZv2xDaP5JamTdZyHqen7NqjQButzCg1DmFBjoggatcjyH5e43",
        "url" : "https://producerooo1.html"
    },
    "beos.prodf":
    {
        "pub_active" : "EOS5fwzBUP2BggwfjAXjR9auHAQRr88MrcxM9a2AZ2tUWBKBG6rFN",
        "prv_active" : "5JExnvDE9QTr8Y6U5HvbuJ9bsq6ZH3CY58DCzSpHCfrA2GwkHen",
        "pub_owner" : "EOS8JjMZSQDcPu81A6FuCfT7TDpA2e8Q4HAc8cUycmD2XRqS6PQLX",
        "prv_owner" : "5KiTii8oCzcRUAkvxLcjhYgF5iSYx6GJGqgL3q5N85aJGvwcwiR",
        "url" : "https://producerooo1.html"
    },
    "beos.prodg":
    {
        "pub_active" : "EOS5MMrUgXxBuv88mYE5a1E6Kxrc9z94fNcxGR7KcVTAH2GshaDHA",
        "prv_active" : "5KMACyNe1LUP1nXCUmRVwxxmrMcqgZGoMfBNTtiJk2eiJaifgj6",
        "pub_owner" : "EOS7gDJAs1u7iHVYSW66i5a7i2GFEAxz9BgGbNmbkJT6k48TAZ4aE",
        "prv_owner" : "5KEaHqKxysg6vzuUp8oihdNj94T1PGfnTtTgDebcAzfMnpFUsCh",
        "url" : "https://producerooo1.html"
    },
    "beos.prodh":
    {
        "pub_active" : "EOS7ZZZecynJqMfK9772rJbzbg4LCsWcKQY3Z6Y5PYg6goDzMS9Pe",
        "prv_active" : "5KDMd6fKCvGQqAyX2ANWzv6UnbEuiKtMEfDU9cYRypp5Gp4oqM9",
        "pub_owner" : "EOS6e4tvpwCUQCyuaMe2LWpNgqT6M1aeNnsL5eNFdWn7qzmHD9YTv",
        "prv_owner" : "5Kb1N9dW8QaSqdauNWz37KvGNfGNH7gkXrcS2N2Sq8PEk8mSvqU",
        "url" : "https://producerooo1.html"
    },
    "beos.prodi":
    {
        "pub_active" : "EOS5LKTzXLVRAAsynEXCq5n1n4M7hA5NCjWCxRYUfLNu5V4rhibf1",
        "prv_active" : "5HtAcQCWhbfJNwDpqa79Lc7MnQbkWXWGebUeYKmx5eXCRBBNcCF",
        "pub_owner" : "EOS64BLU6izGAarFTaMJPamc6AYYbVCaiR8fMBjH4c2mtFBd1hJvc",
        "prv_owner" : "5HtxybWiEMDbVtPxA1DBTkEiRtMZ9WTf9hk6s1wSShRRvUeYxJT",
        "url" : "https://producerooo1.html"
    },
    "beos.prodj":
    {
        "pub_active" : "EOS5wf9WbsNVuduf2df65LBfnV66DryforScMqc1FYcm3VV73J9Bw",
        "prv_active" : "5JPEPTFQua9pWYYY4MkZrS74W5QYpSc4Nm9Ft3gi1be5vKN6QVW",
        "pub_owner" : "EOS6HXaxJB5C4q5RhCroFPyLeygCV1ZvQoxTM8tPkawBTfPuwcyKJ",
        "prv_owner" : "5HzZKZEW6dqnoyr7d6MtVL7E7wnxTP7AT4TR9iT4mwt8esizSHd",
        "url" : "https://producerooo1.html"
    },
    "beos.prodk":
    {
        "pub_active" : "EOS6gcyGSBrAvA9NZwX1DqizDUQ6RVbQBq63ojJkNdYt1yHCAnJNt",
        "prv_active" : "5JLzCHesWks1TDjXXoRyKQ3a18YG46L544zUcSQsGiwsPVPQMpS",
        "pub_owner" : "EOS6Nm9BeKC21AAax11r1hpEaDew2RCvjaCGZP7zxRu2NYh3ri2mt",
        "prv_owner" : "5Jf4Fj9KPhHMXGPjtxUgAD27svQrhU3sSaPZzxWJXgDpSAU4AmB",
        "url" : "https://producerooo1.html"
    },
    "beos.prodl":
    {
        "pub_active" : "EOS7DWdKdMMRTfrBb1jZ1EiW3HodEERspdr2oYSfwpAoBQzWSYbdE",
        "prv_active" : "5JCZJLj7evn1iw4J32g7oPBoj7Qgoq59YX4qiTE2byNPRcVGRkK",
        "pub_owner" : "EOS7k6SQ99Vt4hUytJ2qSWXMJDcWrQx7SLZScMnbHtR1EPJne7qyy",
        "prv_owner" : "5Jpkb5CnzwTqZJ6FWPaPmPy9nD3DCPsSLEpiUbNGe5LTGxuCKbz",
        "url" : "https://producerooo1.html"
    },
    "beos.prodm":
    {
        "pub_active" : "EOS6Ev4j3J5NKVr1cWdoUtYfEroL7XJB7C62URAowvfpCnKPYSJxQ",
        "prv_active" : "5JocuD31sh9epStWmY6MMysQtDsKxTG7cbBxDcujs62v1vkquKa",
        "pub_owner" : "EOS5zRiqqpnt2GFm5NXHvQcjNcGWyfgTwS8iycPptFWh1N1xw8b1U",
        "prv_owner" : "5JtsN7ML25NM6KNvG3Ti77uyLBtTstpVLdboPyE2yHGoSNQrsS9",
        "url" : "https://producerooo1.html"
    },
    "beos.prodn":
    {
        "pub_active" : "EOS7KfF7BdDdaHok6aWdMjY6jjVknTXRzZn3GmRcHuTEWLC5H4K9Q",
        "prv_active" : "5KD2ZbiFp17sV94prz3RTuRJBcrWUxAcPSz5oYUFnHLFGp4z99g",
        "pub_owner" : "EOS7qXHyNYLtbRZ7YS8fF5woRzoEfUNt94uvSM2BLuSEEABVfG9Vn",
        "prv_owner" : "5Ju7JUNTXyA3xdbefCXfsHpw8RELBiCDU3FmMBxDgCPD19oHKPg",
        "url" : "https://producerooo1.html"
    },
    "beos.prodo":
    {
        "pub_active" : "EOS8f75tNFqLFVsm4tdRycLrgSmsRZR3pBkGT5eE7t2PMMTdUBvBn",
        "prv_active" : "5KhQt9xtw1RFD4kuvvTng8sfgHBy3JKu72xjSwVkoWiY741zHe2",
        "pub_owner" : "EOS8fyM1CFWfxC56nEXvtq7ygM32Cx3wtW1EFiNeXhDuYvZSJYYD9",
        "prv_owner" : "5JqCebY8fZzjUiHC2KdpnV1hN8kBaYdX7KVfUmosqAumB6gRRva",
        "url" : "https://producerooo1.html"
    },
    "beos.prodp":
    {
        "pub_active" : "EOS4vWjPK6Kqhc6X4RDrmxbunvpEeMvpwyw4jtzJaTnF3BypoGRMa",
        "prv_active" : "5HyNGnBZCEeHRMiEss3V44xqV1XAwZKtJsPsBcBKByoS4H6K7oj",
        "pub_owner" : "EOS5nMCe9wJDxErgwVz3uUWnfHNdweCq5peLuG68c5qnAUBpEp7T3",
        "prv_owner" : "5KZC5qRXUGsh1cSray1RfFc5wK9YzJUhypjdtPCLTh27JUNphgp",
        "url" : "https://producerooo1.html"
    },
    "beos.prodq":
    {
        "pub_active" : "EOS6AqBTd2qEwb1aM6wTpzGSNfbtfJMz531PUQEEEUGNVU1o3Arno",
        "prv_active" : "5J9UzTcm6hq6HHhuW3PeWtC7prnM8xBzjdVoA1X2YANhhNUcXsB",
        "pub_owner" : "EOS8MeYjvBvEw4FkydHRGiR4fS34TTdxGLWNJpuV8Pa3MZkDkFGF7",
        "prv_owner" : "5JBdk1reLkcewcbMtE5eiAqdsvibGZYwkH7QzxB6tYboqoza2MF",
        "url" : "https://producerooo1.html"
    },
    "beos.prodr":
    {
        "pub_active" : "EOS5mnRExMhdxY24KBR94m2pw7qLF6copjTE8Spvfrdft71Bpg6CL",
        "prv_active" : "5JhmpRj2ZUDeAHQKpskLkvqVP94C97tYRkdrzq7Lyd1PEN76UdU",
        "pub_owner" : "EOS6JwPPdx93Rr1QNt9rnS59vVz2h2PJvNyDhxryc1jBoAccysfaK",
        "prv_owner" : "5JGV2GXnEXfU4suHatbUMpUisBXypdvbVkmaJ8Tr2p6CeFBXwyX",
        "url" : "https://producerooo1.html"
    },
    "beos.prods":
    {
        "pub_active" : "EOS624n1MJPka1rbEDGvw5degcUAAHbpG47792vvEsHuYkLd4TC5i",
        "prv_active" : "5JWEdsDBtDZBzrDwqryVtrz7sSXq2dViieXWaCSQoq3dGTE1iX8",
        "pub_owner" : "EOS55RTefzVQPWhEKjxdTMb3aLm5fVxKLvY2vnVnzC6we2SJBqLgN",
        "prv_owner" : "5JUxJETnPboedq49dZwsH9mNPsNwHBG7mxrsCBqnRvffP2K5dBP",
        "url" : "https://producerooo1.html"
    },
    "beos.prodt":
    {
        "pub_active" : "EOS6XhzFfvYX2E347XZKmpycJ3i5kXDZKHM7GgYa2PNVcDowjCjZh",
        "prv_active" : "5KiS8qUbyoKp5fsxZBZRrWyFJ3rjBku1zHyYLV5TdYQUAmRFSP3",
        "pub_owner" : "EOS5FJbaeYFFHAhfWztV3kq5u3QaV2hb5yUw2tqEgj81gL8T5bUyu",
        "prv_owner" : "5JtbNHsUHuP3YLjbrP641A4GHiMipxd9PBwueVrtvt48h7uuDaU",
        "url" : "https://producerooo1.html"
    },
    "beos.produ":
    {
        "pub_active" : "EOS5y8hrNpCZctcFkTbqAbwZ5NCNnv659c49S2NuP3fKxq9obuDyd",
        "prv_active" : "5KUrW7DktKc3c9ohz9oAqJEGc72tjWR9jqi5Z4Sg9yeyo6953Kg",
        "pub_owner" : "EOS75EgynYb2Y2VPrcRHjw6YuSvFKo4K7Vgie5E7u3dh6wmFw9pZ5",
        "prv_owner" : "5Jok9iascFKEi1WsJ9m5w2iEyDfi5ndq2SxHGFpGEmZnnCS76FN",
        "url" : "https://producerooo1.html"
    }
}

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
# beos.distrib will leave on itself all ram it consumed or given leftover value, whichever is greater (to be used for test stabilization)
DISTRIB_RAM_LEFTOVER = 0
# beos.distrib stores all rewards as net, whatever value is on cpu (declared here) will also be subtracted from net pool of rewards
DISTRIB_NETCPU_LEFTOVER = 10000

#STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION = 1 * 30 * 60 * 2 # 1/2 hour for testing purposes
#STARTING_BLOCK_FOR_BEOS_DISTRIBUTION = 6 * 60 * 2 # 6 minutes (at two blocks per second)
#ENDING_BLOCK_FOR_BEOS_DISTRIBUTION = 1 * 24 * 3600 * 2 # days(98).to_seconds() * 2
#DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_BEOS_DISTRIBUTION = 5 * 60 * 2 # 5 minutes for testing
#TRUSTEE_REWARD_BEOS = CORE_INITIAL_SUPPLY * 2 // 7 # 2/7 of initial supply
#STARTING_BLOCK_FOR_RAM_DISTRIBUTION = 6 * 60 * 2 # 6 minutes (at two blocks per second)
#ENDING_BLOCK_FOR_RAM_DISTRIBUTION = 280 * 24 * 3600 * 2 # days(280).to_seconds() * 2
#DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_RAM_DISTRIBUTION = 5 * 60 * 2 # 5 minutes for testing
#TRUSTEE_REWARD_RAM = 0 # no ram for trustee as reward
STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION = 1800 * 2 
STARTING_BLOCK_FOR_BEOS_DISTRIBUTION = 220 # days(7).to_seconds() * 2
ENDING_BLOCK_FOR_BEOS_DISTRIBUTION =  24 * 3600 * 2 # days(98).to_seconds() * 2
DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_BEOS_DISTRIBUTION = 1 * 600  # hours(1).to_seconds() * 2
TRUSTEE_REWARD_BEOS = CORE_INITIAL_SUPPLY * 2 // 7 # 2/7 of initial supply
STARTING_BLOCK_FOR_RAM_DISTRIBUTION = 220  # days(7).to_seconds() * 2
ENDING_BLOCK_FOR_RAM_DISTRIBUTION = 24 * 3600 * 2 # days(280).to_seconds() * 2
DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_RAM_DISTRIBUTION = 1 * 600  # hours(1).to_seconds() * 2
TRUSTEE_REWARD_RAM = 0 # no ram for trustee as reward

### init loggers
global log_main
log_main =  open(MAIN_LOG_PATH, "a+")
global log_error
log_error = open(ERROR_LOG_PATH, "a+")
