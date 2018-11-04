#!/usr/bin/python3
"""
BEOS deployment script
"""

try:
    import config
except Exception as ex:
    msg = "config.py is not present. Please make a copy of config-example.py and name it as config.py. Edit config.py to customize your build environment."
    print(msg)
    from sys import exit
    exit(1)

try:
    import distro
except Exception as ex:
    msg = "This program requires python-distro package. Please install python-distro package."
    print(msg)
    from sys import exit
    exit(1)

try:
    from git import Repo
except Exception as ex:
    msg = "This program requires python-git package. Please install python-git package."
    print(msg)
    from sys import exit
    exit(1)

import logging
import requests
import os
import subprocess
import sys

MODULE_NAME = "BEOS deploy"

logger = logging.getLogger(MODULE_NAME)
logger.setLevel(config.LOG_LEVEL)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(config.LOG_LEVEL)
ch.setFormatter(logging.Formatter(config.LOG_FORMAT))

fh = logging.FileHandler(os.path.dirname(os.path.abspath(__file__)) + '/beos_deploy.log')
fh.setLevel(config.LOG_LEVEL)
fh.setFormatter(logging.Formatter(config.LOG_FORMAT))

logger.addHandler(ch)
logger.addHandler(fh)

def get_processor_count():
    from multiprocessing import cpu_count
    return cpu_count()

def install_system_packages():
    logger.info("=== Checking for system packages")
    platform_name, platform_version, platform_type =  distro.linux_distribution(full_distribution_name = False)
    logger.info("Detected platform: {0} {1} {2}".format(platform_name, platform_version, platform_type))
    if platform_name == "ubuntu":
        packages = ["clang-4.0", "lldb-4.0", "libclang-4.0-dev", "cmake", "make", "libbz2-dev", "libssl-dev", "libgmp3-dev", "autotools-dev", "build-essential", "libbz2-dev", "libicu-dev", "python-dev", "autoconf", "libtool", "git", "mongodb", "lcov"]
        if platform_version == "18.04":
            packages.append("mongodb-server-core")
        for package in packages:
            logger.info("Checking package {0}".format(package))
            params = ["dpkg-query", "-f", "${Status}\n", "-W", package]
            ret = subprocess.run(params,  stdout=subprocess.PIPE)
            retcode = ret.returncode
            stdout = str(ret.stdout.decode('utf-8')).strip()
            if retcode == 0 and stdout == "install ok installed":
                logger.info("Package {0} is already installed".format(package))
            else:
                logger.info("Package {0} is not installed, installing".format(package))
                params = ["sudo", "apt", "-y", "install", package]
                ret = subprocess.run(params)
                retcode = ret.returncode
                if retcode == 0:
                    logger.info("Package {0} has been installed".format(package))
                else:
                    logger.error("Error installing {0}".format(package))
                    sys.exit(1)
    else:
        logger.error("Platform {0} is not supported at the moment.")
        from sys import exit
        exit(1)

def install_boost():
    logger.info("=== Checking for Boost")
    # check if BOOST_ROOT env is present
    cmake_options = dict()
    boost_root = os.environ.get("BOOST_ROOT", None)
    if boost_root is not None:
        logger.info("BOOST_ROOT is set to: {0}".format(boost_root))
        cmake_options["BOOST_ROOT"] = boost_root
        return cmake_options
    # check if boost is installed in BOOST_INSTALL_DIR
    if os.path.exists(config.BOOST_INSTALL_DIR):
        logger.info("Boost is already installed in: {0}".format(config.BOOST_INSTALL_DIR))    
        cmake_options["BOOST_ROOT"] = config.BOOST_INSTALL_PREFIX
        return cmake_options
    # installing boost from sources
    logger.info("Boost libraries not detected attempting to install")
    boost_download_url = "https://sourceforge.net/projects/boost/files/boost/1.67.0/boost_1_67_0.tar.bz2/download"
    boost_archive_name = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "boost_1.67.0.tar.bz2")
    boost_source_dir = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "boost_1_67_0")
    boost_root = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "boost_1_67_0")
    
    logger.info("Downloading boost...")
    res = requests.get(boost_download_url)
    with open(boost_archive_name, 'wb') as f:
        f.write(res.content)

    logger.info("Decompressing boost...")
    import tarfile
    boost_tar = tarfile.open(boost_archive_name, mode = 'r:bz2')
    boost_tar.extractall(boost_source_dir)
    
    logger.info("Bootstraping boost..")
    params = ["./bootstrap.sh", "--prefix", config.BOOST_INSTALL_PREFIX]
    ret = subprocess.run(params, cwd = boost_root)
    if ret.returncode != 0:
        logger.error("bootstrap command failed. Please inspect log files for more information.")
        sys.exit(1)
    
    logger.info("Installing boost..")
    params = ["sudo", "./b2", "install"]
    ret = subprocess.run(params, cwd = boost_root)
    if ret.returncode != 0:
        logger.error("sudo b2 install command failed. Please inspect log files for more information.")
        sys.exit(1)
    
    cmake_options["BOOST_ROOT"] = config.BOOST_INSTALL_PREFIX
    os.environ["BOOST_ROOT"] = config.BOOST_INSTALL_PREFIX
    return cmake_options

def install_mongo_driver():
    logger.info("=== Checking for Mongo C Driver and Mongo CXX Driver")
    if os.path.exists(config.MONGO_C_INSTALL_DIR):
        logger.info("Mongo C driver is already installed")
    else:
        mongoc_url = "https://github.com/mongodb/mongo-c-driver/releases/download/1.13.0/mongo-c-driver-1.13.0.tar.gz"
        mongoc_archive_name = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "mongo-c-driver-1.13.0.tar.gz")
        mongoc_root = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "mongo-c-driver-1.13.0")

        logger.info("Downloading Mongo C driver...")
        res = requests.get(mongoc_url)
        with open(mongoc_archive_name, 'wb') as f:
            f.write(res.content)

        logger.info("Decompressing Mongo C driver...")
        import tarfile
        mongoc_tar = tarfile.open(mongoc_archive_name, 'r:gz')
        mongoc_tar.extractall(config.SOURCES_DOWNLOAD_DIR)

        if not os.path.exists("{0}/{1}".format(mongoc_root, "build")):
            from os import makedirs
            makedirs("{0}/{1}".format(mongoc_root, "build"))

        logger.info("Running cmake...")
        params = ["cmake", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX={0}".format(config.MONGO_C_INSTALL_PREFIX), ".."]
        ret = subprocess.run(params, cwd = "{0}/{1}".format(mongoc_root, "build"))
        if ret.returncode != 0:
            logger.error("Cmake command failed. Please inspect log files for more information.")
            sys.exit(1)

        logger.info("Running make...")
        params = ["make"]
        pcnt = get_processor_count()
        if pcnt > 1:
            params.append("-j{0}".format(pcnt))
        ret = subprocess.run(params, cwd = "{0}/{1}".format(mongoc_root, "build"))
        if ret.returncode != 0:
            logger.error("make command failed. Please inspect log files for more information.")
            sys.exit(1)

        logger.info("Installing Mongo C drivers")
        params = ["sudo", "make", "install"]
        ret = subprocess.run(params, cwd = "{0}/{1}".format(mongoc_root, "build"))
        if ret.returncode != 0:
            logger.error("sudo make install command failed. Please inspect log files for more information.")
            sys.exit(1)

    if os.path.exists(config.MONGO_CXX_INSTALL_DIR):
        logger.info("Mongo CXX driver is already installed")
    else:
        mongocxx_git_url = "https://github.com/mongodb/mongo-cxx-driver.git"
        mongocxx_root = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "mongo-cxx-driver")
        logger.info("Cloning Mongo CXX sources")
        Repo.clone_from(mongocxx_git_url, mongocxx_root,  branch = "releases/stable", depth = 1)

        logger.info("Running cmake...")
        params = ["cmake", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX={0}".format(config.MONGO_C_INSTALL_PREFIX), ".."]
        ret = subprocess.run(params, cwd = "{0}/{1}".format(mongocxx_root, "build"))
        if ret.returncode != 0:
            logger.error("Cmake command failed. Please inspect log files for more information.")
            sys.exit(1)

        logger.info("Running make...")
        params = ["make"]
        pcnt = get_processor_count()
        if pcnt > 1:
            params.append("-j{0}".format(pcnt))
        ret = subprocess.run(params, cwd = "{0}/{1}".format(mongocxx_root, "build"))
        if ret.returncode != 0:
            logger.error("make command failed. Please inspect log files for more information.")
            sys.exit(1)

        logger.info("Installing Mongo CXX drivers")
        params = ["sudo", "make", "install"]
        ret = subprocess.run(params, cwd = "{0}/{1}".format(mongocxx_root, "build"))
        if ret.returncode != 0:
            logger.error("sudo make install command failed. Please inspect log files for more information.")
            sys.exit(1)

def install_secp256k1_zkp():
    logger.info("=== Checking for secp256k1")
    if os.path.exists("{0}/{1}".format(config.SECP256_INSTALL_PREFIX, "include/secp256k1.h")):
        logger.info("secp256k1 is already installed")
        return

    logger.info("secp256k1 is not installed. Performing installation...")
    secp256k1_url = "https://github.com/cryptonomex/secp256k1-zkp.git"
    secp256k1_root = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "secp256k1-zkp")
    
    from git import Repo
    Repo.clone_from(secp256k1_url, secp256k1_root,  branch = "releases/stable", depth = 1)

    logger.info("Running autogen.sh...")
    params = ["./autogen.sh"]
    ret = subprocess.run(params, cwd = secp256k1_root)
    if ret.returncode != 0:
        logger.error("Cmake command failed. Please inspect log files for more information.")
        sys.exit(1)

    logger.info("Running configure...")
    params = ["./configure", "--prefix", config.SECP256_INSTALL_PREFIX]
    ret = subprocess.run(params, cwd = secp256k1_root)
    if ret.returncode != 0:
        logger.error("configure command failed. Please inspect log files for more information.")
        sys.exit(1)

    logger.info("Running make...")
    params = ["make"]
    pcnt = get_processor_count()
    if pcnt > 1:
        params.append("-j{0}".format(pcnt))
    ret = subprocess.run(params, cwd = secp256k1_root)
    if ret.returncode != 0:
        logger.error("make command failed. Please inspect log files for more information.")
        sys.exit(1)

    logger.info("Installing secp256k1-zkp")
    params = ["sudo", "make", "install"]
    ret = subprocess.run(params, cwd = secp256k1_root)
    if ret.returncode != 0:
        logger.error("Sudo make install command failed. Please inspect log files for more information.")
        sys.exit(1)

def install_wasm():
    logger.info("=== Checking for WASM")
    wasm_source_dir = "wasm"
    wasm_llvm_url = "https://github.com/llvm-mirror/llvm.git"
    wasm_clang_url = "https://github.com/llvm-mirror/clang.git"
    wasm_root = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, wasm_source_dir)
    cmake_options = dict()
    if os.path.exists(config.WASM_INSTALL_DIR):
        logger.info("WASM is already installed")
        cmake_options["WASM_ROOT"] = config.WASM_INSTALL_DIR
        os.environ["WASM_ROOT"] = config.WASM_INSTALL_DIR
        return cmake_options
    
    Repo.clone_from(wasm_llvm_url, wasm_root + "/llvm",  branch = "release_40", depth = 1)
    Repo.clone_from(wasm_clang_url, wasm_root + "/llvm/tools/clang",  branch = "release_40", depth = 1)
    
    wasm_build_dir = wasm_root + "/llvm/build"
    if not os.path.exists(wasm_build_dir):
        from os import makedirs
        makedirs(wasm_build_dir)
        
    params = ["cmake", "-G", "Unix Makefiles", "-DCMAKE_INSTALL_PREFIX={0}".format(config.WASM_INSTALL_DIR), "-DLLVM_TARGETS_TO_BUILD=", "-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly", "-DCMAKE_BUILD_TYPE=Release", ".."]
    ret = subprocess.run(params, cwd = wasm_build_dir)
    if ret.returncode != 0:
        logger.error("Cmake command failed. Please inspect log files for more information.")
        sys.exit(1)

    logger.info("Running make...")
    params = ["make"]
    pcnt = get_processor_count()
    if pcnt > 1:
        params.append("-j{0}".format(pcnt))
    ret = subprocess.run(params, cwd = wasm_build_dir)
    if ret.returncode != 0:
        logger.error("make command failed. Please inspect log files for more information.")
        sys.exit(1)

    logger.info("Installing secp256k1-zkp")
    params = ["sudo", "make", "install"]
    ret = subprocess.run(params, cwd = wasm_build_dir)
    if ret.returncode != 0:
        logger.error("sudo make install command failed. Please inspect log files for more information.")
        sys.exit(1)

    cmake_options["WASM_ROOT"] = config.WASM_INSTALL_DIR
    os.environ["WASM_ROOT"] = config.WASM_INSTALL_DIR
    return cmake_options

def install_libraries():
    install_system_packages()
    install_boost()
    install_mongo_driver()
# Not needed - proper version of this library is a part of eos now.
#    install_secp256k1_zkp()
    install_wasm()

def install_eosio(c_compiler, cxx_compiler):
    build_eosio(c_compiler, cxx_compiler)
    logger.info("Running make install {0}".format(config.BEOS_BUILD_DIR))
    params = ["sudo", "make", "install"]
    ret = subprocess.run(params, cwd = config.BEOS_BUILD_DIR, stdout=config.log_main, stderr=config.log_error)
    if ret.returncode != 0:
        logger.error("Make install command failed. Please inspect log files for more information.")
        sys.exit(1)

def build_eosio(c_compiler, cxx_compiler):
    # check if build dir exists, if not make one
    if not os.path.exists(config.BEOS_BUILD_DIR):
        os.makedirs(config.BEOS_BUILD_DIR)
    # calling cmake
    params = [
        "cmake",
        "-DCMAKE_BUILD_TYPE={0}".format(config.EOSIO_BUILD_TYPE),
        "-DCMAKE_CXX_COMPILER={0}".format(cxx_compiler),
        "-DCMAKE_C_COMPILER={0}".format(c_compiler),
        "-DWASM_ROOT={0}".format(config.WASM_INSTALL_DIR),
        "-DCORE_SYMBOL_NAME={0}".format(config.CORE_SYMBOL_NAME),
        "-DOPENSSL_ROOT_DIR={0}".format(config.OPENSSL_ROOT_DIR),
        "-DBUILD_MONGO_DB_PLUGIN={0}".format(config.BUILD_MONGO_DB_PLUGIN),
        "-DENABLE_COVERAGE_TESTING={0}".format(config.ENABLE_COVERAGE_TESTING),
        "-DBUILD_DOXYGEN={0}".format(config.DOXYGEN),
        "-DCMAKE_INSTALL_PREFIX={0}".format(config.EOSIO_INSTALL_PREFIX),
        "-DEOSIO_ROOT_KEY={0}".format(config.EOSIO_PUBLIC_KEY),
        "-DGATEWAY_ROOT_KEY={0}".format(config.BEOS_GATEWAY_PUBLIC_KEY),
        "-DDISTRIBUTION_ROOT_KEY={0}".format(config.BEOS_DISTRIB_PUBLIC_KEY),
        config.BEOS_DIR
    ]
    logger.info("Running cmake with params {0}".format(" ".join(params)))
    ret = subprocess.run(params, cwd = config.BEOS_BUILD_DIR, stdout=config.log_main, stderr=config.log_error)
    if ret.returncode != 0:
        logger.error("Cmake command failed. Please inspect log files for more information.")
        sys.exit(1)
    
    logger.info("Running make in {0}".format(config.BEOS_BUILD_DIR))
    params = ["make"]
    pcnt = get_processor_count()
    if pcnt > 1:
        params.append("-j{0}".format(pcnt))
    ret = subprocess.run(params, cwd = config.BEOS_BUILD_DIR, stdout=config.log_main, stderr=config.log_error)
    if ret.returncode != 0:
        logger.error("make command failed. Please inspect log files for more information.")
        sys.exit(1)

def install_beos(c_compiler, cxx_compiler):
    #
    configure_eosio_init()
    install_eosio(c_compiler, cxx_compiler)

def build_beos(c_compiler, cxx_compiler):
    #
    configure_eosio_init()
    #
    configure_config_ini()
    #
    configure_genesis_json()
    #
    build_eosio(c_compiler, cxx_compiler)

def configure_eosio_init():
    eosio_init_opt = {
        "PROXY_ASSET_PRECISION" : config.PROXY_ASSET_PRECISION,
        "PROXY_ASSET_NAME" : config.PROXY_ASSET_NAME,
        "STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION" : config.STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION,
        "STARTING_BLOCK_FOR_BEOS_DISTRIBUTION" : config.STARTING_BLOCK_FOR_BEOS_DISTRIBUTION,
        "ENDING_BLOCK_FOR_BEOS_DISTRIBUTION" : config.ENDING_BLOCK_FOR_BEOS_DISTRIBUTION,
        "DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_BEOS_DISTRIBUTION" : config.DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_BEOS_DISTRIBUTION,
        "AMOUNT_OF_REWARD_BEOS" : config.AMOUNT_OF_REWARD_BEOS,
        "STARTING_BLOCK_FOR_RAM_DISTRIBUTION" : config.STARTING_BLOCK_FOR_RAM_DISTRIBUTION,
        "ENDING_BLOCK_FOR_RAM_DISTRIBUTION" : config.ENDING_BLOCK_FOR_RAM_DISTRIBUTION,
        "DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_RAM_DISTRIBUTION" : config.DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_RAM_DISTRIBUTION,
        "AMOUNT_OF_REWARD_RAM" : config.AMOUNT_OF_REWARD_RAM,
        "STARTING_BLOCK_FOR_TRUSTEE_DISTRIBUTION" : config.STARTING_BLOCK_FOR_TRUSTEE_DISTRIBUTION,
        "ENDING_BLOCK_FOR_TRUSTEE_DISTRIBUTION" : config.ENDING_BLOCK_FOR_TRUSTEE_DISTRIBUTION,
        "DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_TRUSTEE_DISTRIBUTION" : config.DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_TRUSTEE_DISTRIBUTION,
        "AMOUNT_OF_REWARD_TRUSTEE" : config.AMOUNT_OF_REWARD_TRUSTEE
    }

    eosio_init_src = config.BEOS_DIR + "/contracts/eosio.init/eosio.init.hpp.in"
    eosio_init_dst = config.BEOS_DIR + "/contracts/eosio.init/eosio.init.hpp"
    dst = None
    with open(eosio_init_src, "r") as in_f:
        from string import Template
        src = Template(in_f.read())
        dst = src.substitute(eosio_init_opt)
    with open(eosio_init_dst, "w") as out_f:
        out_f.write(dst)

def configure_config_ini():
    ini_opt = {
        "HTTP_SERVER_PORT" : "http://{0}:{1}".format(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT),
        "EOSIO_PUBLIC_KEY" : config.EOSIO_PUBLIC_KEY,
        "SIGNATURE_PROVIDER" : "{0}=KEOSD:https://{1}:{2}/v1/wallet/sign_digest".format(config.EOSIO_PUBLIC_KEY, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT),
        "WALLET_DIR" : config.DEFAULT_WALLET_DIR
    }
    ini_src = os.path.dirname(os.path.abspath(__file__)) + "/resources/config.ini.in"
    ini_dst = os.path.dirname(os.path.abspath(__file__)) + "/resources/config.ini"
    with open(ini_src, "r") as in_f:
        from string import Template
        src = Template(in_f.read())
        dst = src.substitute(ini_opt)
    with open(ini_dst, "w") as out_f:
        out_f.write(dst)

def configure_genesis_json():
    json_opt = {
        "INITIAL_KEY" : "{0}".format(config.EOSIO_PUBLIC_KEY)
    }
    json_src = os.path.dirname(os.path.abspath(__file__)) + "/resources/genesis.json.in"
    json_dst = os.path.dirname(os.path.abspath(__file__)) + "/resources/genesis.json"
    with open(json_src, "r") as in_f:
        from string import Template
        src = Template(in_f.read())
        dst = src.substitute(json_opt)
    with open(json_dst, "w") as out_f:
        out_f.write(dst)

def initialize_beos():
    import eosio
    try:
        eosio.run_keosd(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT, config.DEFAULT_WALLET_DIR)
        eosio.create_wallet("http://{0}:{1}".format(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT), True)
        eosio.run_nodeos(0, "eosio", config.EOSIO_PUBLIC_KEY)

        eosio.create_account("eosio", "eosio.msig", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio.create_account("eosio", "eosio.names", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio.create_account("eosio", "eosio.saving", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio.create_account("eosio", "eosio.vpay", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio.create_account("eosio", "eosio.unregd", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        
        eosio.create_account("eosio", "eosio.bpay", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)

        eosio.create_account("eosio", "eosio.ram", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio.create_account("eosio", "eosio.ramfee", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio.create_account("eosio", "eosio.stake", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)

        eosio.create_account("eosio", "eosio.token", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio.create_account("eosio", "beos.init", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY)

        eosio.set_contract("eosio.token", config.CONTRACTS_DIR + "/eosio.token", "eosio.token")

        eosio.push_action("eosio.token", "create", '[ "beos.distrib", "{0} {1}"]'.format(config.CORE_INITIAL_AMOUNT, config.CORE_SYMBOL_NAME), "eosio.token")
        eosio.push_action("eosio.token", "create", '[ "beos.gateway", "{0} {1}"]'.format(config.PROXY_INITIAL_AMOUNT, config.PROXY_ASSET_NAME), "eosio.token")

        eosio.set_contract("eosio", config.CONTRACTS_DIR + "eosio.system", "eosio")
        eosio.set_contract("beos.init", config.CONTRACTS_DIR + "eosio.init", "beos.init")
        eosio.set_contract("beos.gateway", config.CONTRACTS_DIR + "eosio.gateway", "beos.gateway")
        eosio.set_contract("beos.distrib", config.CONTRACTS_DIR + "eosio.distribution", "beos.distrib")

        eosio.push_action("eosio", "initram", '[ "beos.gateway", "{0}"]'.format(config.INIT_RAM), "eosio")

        eosio.terminate_running_tasks()
        eosio.show_keosd_postconf(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT, config.DEFAULT_WALLET_DIR)
        eosio.show_wallet_unlock_postconf()
        eosio.show_nodeos_postconf(0, "eosio", config.EOSIO_PUBLIC_KEY)
    except eosio.EOSIOException as ex:
        eosio.terminate_running_tasks()
        logger.error("Exception during initialize: {0}".format(ex))
        sys.exit(1)

def make_integration_test():
    if os.path.exists(config.BEOS_BUILD_DIR + "/Makefile"):
        logger.info("Running integration tests")
        params = ["make", "test"]
        subprocess.run(params, cwd = config.BEOS_BUILD_DIR, stdout=config.log_main, stderr=config.log_error)
    else:
        logger.error("Makefile does not exists in {0}, calling make test will not work.".format(config.BEOS_BUILD_DIR))

def make_unit_test():
    logger.info("Running unit tests")
    tests_working_dir = "{0}/{1}".format(config.BEOS_BUILD_DIR, "unittests/")
    params = ["./unit_test"]
    subprocess.run(params, cwd = tests_working_dir, stdout=config.log_main, stderr=config.log_error)

def make_beos_plugin_test():
    logger.info("Running BEOS plugin tests")
    tests_working_dir = "{0}/{1}".format(config.BEOS_BUILD_DIR, "tests/beos_plugin_tests/")
    params = ["./test01.py", "--main-dir", config.BEOS_BUILD_DIR]
    subprocess.run(params, cwd = tests_working_dir, stdout=config.log_main, stderr=config.log_error)

# Disabled as requeste by mtrela
#    params = ["./test02.py", "--main-dir", config.BEOS_BUILD_DIR]
#    subprocess.run(params, cwd = tests_working_dir, stdout=config.log_main, stderr=config.log_error)

    params = ["./test03.py", "--main-dir", config.BEOS_BUILD_DIR]
    subprocess.run(params, cwd = tests_working_dir, stdout=config.log_main, stderr=config.log_error)

if __name__ == '__main__':
    from optparse import OptionParser, OptionGroup
    parser = OptionParser(usage = "Usage: %prog options")

    generalGroup = OptionGroup(parser, "General actions")
    generalGroup.add_option("--download-sources", action="store_true", dest="download_sources", help="Delete source tree and clone sources from git repository.")
    generalGroup.add_option("--c-compiler", action="store", type="string", default=config.DEFAULT_C_COMPILER, dest="c_compiler", help="Set C compiler")
    generalGroup.add_option("--cxx-compiler", action="store", type="string", default=config.DEFAULT_CXX_COMPILER, dest="cxx_compiler", help="Set CXX compiler")

    librariesGroup = OptionGroup(parser, "Libraries and system requirements actions")
    librariesGroup.add_option("--install-system-packages", action="store_true", dest="install_system_packages", help="Install system packages available in system repositories.")
    librariesGroup.add_option("--install-boost", action="store_true", dest="install_boost", help="Install newest version of the boost library.")
    librariesGroup.add_option("--install-mongo-driver", action="store_true", dest="install_mongo_driver", help="Install C and C++ drivers for MongoDB.")
# Not needed - proper version of this library is a part of eos now.
#    librariesGroup.add_option("--install-secp256k1-zkp", action="store_true", dest="install_secp256k1_zkp", help="Install SCEP256K1 library.")
    librariesGroup.add_option("--install-wasm", action="store_true", dest="install_wasm", help="Install WASM compiler.")
    librariesGroup.add_option("--install-libraries", action="store_true", dest="install_libraries", help="Install boost, mongo plugin, secp256k1 library and WASM compiler in one step.")

    buildGroup = OptionGroup(parser, "BEOS/EOSIO building and installing actions")
    buildGroup.add_option("--install-eosio", action="store_true", dest="install_eosio", help="Build EOSIO and install it to the specified directory.")
    buildGroup.add_option("--build-eosio", action="store_true", dest="build_eosio", help="Build EOSIO without installing.")

    buildGroup.add_option("--install-all", action="store_true", dest="install_all", help="Install all required packages, build EOSIO with BEOS and install it to specyfied path")
    buildGroup.add_option("--install-beos", action="store_true", dest="install_beos", help="Build EOSIO with BEOS and install it to specyfied path")
    buildGroup.add_option("--build-beos", action="store_true", dest="build_beos", help="Build EOSIO with BEOS without installing")

    postinstallGroup = OptionGroup(parser, "Postinstallation actions")
    postinstallGroup.add_option("--initialize-beos", action="store_true", dest="initialize_beos", help="Runs executable and creates system accounts.")
    postinstallGroup.add_option("--create-genesis-and-config", action="store_true", dest="create_genesis_and_config", help="Creates genesis.json and config.ini files.")

    testsGroup = OptionGroup(parser, "Installation testing actions")
    testsGroup.add_option("--make-integration-test", action="store_true", dest="make_integration_test", help="Run main EOSIO tests")
    testsGroup.add_option("--make-unit-test", action="store_true", dest="make_unit_test", help="Run suit of unit tests")
    testsGroup.add_option("--make-beos-plugin-test", action="store_true", dest="make_beos_plugin_test", help="Run BEOS plugin tests")

    parser.add_option_group(generalGroup)
    parser.add_option_group(librariesGroup)
    parser.add_option_group(buildGroup)
    parser.add_option_group(postinstallGroup)
    parser.add_option_group(testsGroup)

    (options, args) = parser.parse_args()
    
    from sys import argv, exit
    if len(argv) == 1:
        parser.print_help()
        exit(0)

    if options.download_sources:
        logger.info("Cloning sources from repository {0} to {1}".format(config.BEOS_REPOSITORY_PATH, config.BEOS_DIR))
        beos_repo = None
        if os.path.exists(config.BEOS_DIR):
            beos_repo = Repo(config.BEOS_DIR)
            beos_repo.remotes.origin.pull()
            beos_repo.git.submodule('update', '--init', '--recursive')
        else:
            beos_repo = Repo.clone_from(config.BEOS_REPOSITORY_PATH, config.BEOS_DIR, branch = config.BEOS_REPOSITORY_BRANCH)
            beos_repo.git.submodule('update', '--init', '--recursive')
    
    c_compiler = options.c_compiler
    cxx_compiler = options.cxx_compiler

    if options.install_system_packages:
        install_system_packages()

    if options.install_boost:
        install_boost()

    if options.install_mongo_driver:
        install_mongo_driver()

# Not needed - proper version of this library is a part of eos now.
#    if options.install_secp256k1_zkp:
#        install_secp256k1_zkp()

    if options.install_wasm:
        install_wasm()

    if options.install_libraries:
        install_libraries()

    from sys import exit
    if os.path.exists(config.BEOS_DIR):
        if os.path.isdir(config.BEOS_DIR):
            if not os.listdir(config.BEOS_DIR):
                logger.error("{0} is empty. Please run: deploy.py with --download-sources option".format(config.BEOS_DIR))
                exit(1)
        else:
            logger.error("{0} is not a directory.".format(config.BEOS_DIR))
            exit(1)
    else:
        logger.error("{0} does not exists.".format(config.BEOS_DIR))
        exit(1)

    if options.install_eosio:
        install_eosio(c_compiler, cxx_compiler)

    if options.build_eosio:
        build_eosio(c_compiler, cxx_compiler)
        
    if options.install_all:
        install_libraries()
        install_beos(c_compiler, cxx_compiler)
        
    if options.install_beos:
        install_beos(c_compiler, cxx_compiler)

    if options.build_beos:
        build_beos(c_compiler, cxx_compiler)

    if options.make_integration_test:
        make_integration_test()

    if options.make_unit_test:
        make_unit_test()

    if options.make_beos_plugin_test:
        make_beos_plugin_test()

    if options.create_genesis_and_config:
        configure_config_ini()
        configure_genesis_json()

    if options.initialize_beos:
        initialize_beos()

    # close loggers
    config.log_main.close()
    config.log_error.close()
