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
import time

MODULE_NAME = "BEOS deploy"

logger = logging.getLogger(MODULE_NAME)
logger.setLevel(config.LOG_LEVEL)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(config.LOG_LEVEL)
ch.setFormatter(logging.Formatter(config.LOG_FORMAT))

fh = logging.FileHandler(config.MAIN_LOG_PATH)
fh.setLevel(config.LOG_LEVEL)
fh.setFormatter(logging.Formatter(config.LOG_FORMAT))

logger.addHandler(ch)
logger.addHandler(fh)

def run_command(parameters, working_dir, run_shell = False):
    ret = subprocess.run(parameters, cwd = working_dir, shell = run_shell, stdout=config.log_main, stderr=config.log_main)
    retcode = ret.returncode
    if retcode == 0:
        logger.debug("Executed with ret: {0}".format(ret))
    else:
        logger.error("Executed with ret: {0}".format(ret))
        logger.error("{0} command failed. Please inspect log files for more information.".format(" ".join(parameters)))
        sys.exit(1)

def get_processor_count():
    from multiprocessing import cpu_count
    return cpu_count()
    #return 4 # :D

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
    boost_root = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "boost_1_67_0")

    logger.info("Downloading boost...")
    res = requests.get(boost_download_url)
    with open(boost_archive_name, 'wb') as f:
        f.write(res.content)

    logger.info("Decompressing boost...")
    import tarfile
    boost_tar = tarfile.open(boost_archive_name, mode = 'r:bz2')
    boost_tar.extractall(config.SOURCES_DOWNLOAD_DIR)

    logger.info("Bootstraping boost..")
    params = ["./bootstrap.sh", "--prefix={0}".format(config.BOOST_INSTALL_PREFIX)]
    run_command(params, boost_root)

    logger.info("Installing boost..")
    params = ["sudo", "./b2", "install"]
    run_command(params, boost_root)

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
        run_command(params, "{0}/{1}".format(mongoc_root, "build"))

        logger.info("Running make...")
        params = ["sudo", "make"]
        pcnt = get_processor_count()
        if pcnt > 1:
            params.append("-j{0}".format(pcnt))
        run_command(params, "{0}/{1}".format(mongoc_root, "build"))

        logger.info("Installing Mongo C drivers")
        params = ["sudo", "make", "install"]
        run_command(params, "{0}/{1}".format(mongoc_root, "build"))

    if os.path.exists(config.MONGO_CXX_INSTALL_DIR):
        logger.info("Mongo CXX driver is already installed")
    else:
        mongocxx_git_url = "https://github.com/mongodb/mongo-cxx-driver.git"
        mongocxx_root = "{0}/{1}".format(config.SOURCES_DOWNLOAD_DIR, "mongo-cxx-driver")
        logger.info("Cloning Mongo CXX sources")
        try:
            Repo.clone_from(mongocxx_git_url, mongocxx_root,  branch = "releases/stable", depth = 1)
        except Exception as ex:
            logger.error(ex)
            sys.exit(1)

        logger.info("Running cmake...")
        params = ["cmake", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX={0}".format(config.MONGO_C_INSTALL_PREFIX), ".."]
        run_command(params, "{0}/{1}".format(mongocxx_root, "build"))

        logger.info("Running make...")
        # for some weird reason it need sudo!
        params = ["sudo", "make"]
        pcnt = get_processor_count()
        if pcnt > 1:
            params.append("-j{0}".format(pcnt))
        run_command(params, "{0}/{1}".format(mongocxx_root, "build"))

        logger.info("Installing Mongo CXX drivers")
        params = ["sudo", "make", "install"]
        run_command(params, "{0}/{1}".format(mongocxx_root, "build"))

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
    try:
        Repo.clone_from(wasm_llvm_url, wasm_root + "/llvm",  branch = "release_40", depth = 1)
        Repo.clone_from(wasm_clang_url, wasm_root + "/llvm/tools/clang",  branch = "release_40", depth = 1)
    except Exception as ex:
        logger.error(ex)
        sys.exit(1)

    platform_name, platform_version, platform_type =  distro.linux_distribution(full_distribution_name = False)
    if platform_name == "ubuntu":
        if platform_version == "18.10":
            run_command(['sh', '-c','curl https://bugzilla.redhat.com/attachment.cgi?id=1389687 | patch -p1'], wasm_root + '/llvm')

    wasm_build_dir = wasm_root + "/llvm/build"
    if not os.path.exists(wasm_build_dir):
        from os import makedirs
        makedirs(wasm_build_dir)

    params = ["cmake", "-G", "Unix Makefiles", "-DCMAKE_INSTALL_PREFIX={0}".format(config.WASM_INSTALL_DIR), "-DLLVM_TARGETS_TO_BUILD=", "-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly", "-DCMAKE_BUILD_TYPE=Release", ".."]
    run_command(params, wasm_build_dir)

    logger.info("Running make...")
    params = ["make"]
    pcnt = get_processor_count()
    if pcnt > 1:
        params.append("-j{0}".format(pcnt))
    run_command(params, wasm_build_dir)

    logger.info("Installing WASM")
    params = ["sudo", "make", "install"]
    run_command(params, wasm_build_dir)

    cmake_options["WASM_ROOT"] = config.WASM_INSTALL_DIR
    os.environ["WASM_ROOT"] = config.WASM_INSTALL_DIR
    return cmake_options

def install_libraries():
    install_system_packages()
    install_boost()
    install_mongo_driver()
    install_wasm()

def install_eosio(c_compiler, cxx_compiler):
    build_eosio(c_compiler, cxx_compiler)
    logger.info("Running make install {0}".format(config.BEOS_BUILD_DIR))
    params = ["sudo", "make", "install"]
    run_command(params, config.BEOS_BUILD_DIR)

def build_eosio(c_compiler, cxx_compiler):
    # check if build dir exists, if not make one
    if not os.path.exists(config.BEOS_BUILD_DIR):
        os.makedirs(config.BEOS_BUILD_DIR)
    # check if Makefile exists in build dir, if yes we will call make clean, cmake, and make
    #if os.path.exists(config.BEOS_BUILD_DIR + "/Makefile"):
    #    logger.info("Running make clean in {0}".format(config.BEOS_BUILD_DIR))
    #    params = ["make", "clean"]
    #    subprocess.run(params, cwd = config.BEOS_BUILD_DIR, stdout=config.log_main, stderr=config.log_main)
    # calling cmake
    params = [
        "cmake",
        "-DCMAKE_BUILD_TYPE={0}".format(config.EOSIO_BUILD_TYPE),
        "-DCMAKE_CXX_COMPILER={0}".format(cxx_compiler),
        "-DCMAKE_C_COMPILER={0}".format(c_compiler),
        "-DWASM_ROOT={0}".format(config.WASM_INSTALL_DIR),
        "-DCORE_SYMBOL_NAME={0}".format(config.CORE_SYMBOL_NAME),
        "-DOPENSSL_ROOT_DIR={0}".format(config.OPENSSL_ROOT_DIR),
        "-DBOOST_ROOT={0}".format(config.BOOST_INSTALL_DIR),
        "-DBUILD_MONGO_DB_PLUGIN={0}".format(config.BUILD_MONGO_DB_PLUGIN),
        "-DENABLE_COVERAGE_TESTING={0}".format(config.ENABLE_COVERAGE_TESTING),
        "-DBUILD_DOXYGEN={0}".format(config.DOXYGEN),
        "-DCMAKE_INSTALL_PREFIX={0}".format(config.EOSIO_INSTALL_PREFIX),
        "-DEOSIO_ROOT_KEY={0}".format(config.EOSIO_PUBLIC_KEY),
        "-DGATEWAY_ROOT_KEY={0}".format(config.BEOS_GATEWAY_PUBLIC_KEY),
        "-DDISTRIBUTION_ROOT_KEY={0}".format(config.BEOS_DISTRIB_PUBLIC_KEY),
        "-DSTARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION={0}".format(config.STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION),
        "-DDISTRIBUTION_PARAMS={0}".format(config.DISTRIBUTION_PARAMS),
        "-DGATEWAY_PARAMS={0}".format(config.GATEWAY_PARAMS),
        "-DNODEOS_HTTP_SERVER_PORT={0}".format("{0}:{1}".format(config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)),
        "-DSIGNATURE_PROVIDER={0}".format("{0}=KEOSD:http://{1}:{2}/v1/wallet/sign_digest".format(config.EOSIO_PUBLIC_KEY, config.KEOSD_IP_ADDRESS, config.KEOSD_PORT)),
        "-DDISABLE_FAILING_TESTS={0}".format(config.DISABLE_FAILING_TESTS),
        "-DDISABLE_WASM_TESTS={0}".format(config.DISABLE_WASM_TESTS),
        "-DWALLET_PASSWORD_PATH={0}".format(config.WALLET_PASSWORD_PATH),
        "-DDEFAULT_WALLET_DIR={0}".format(config.DEFAULT_WALLET_DIR),
        "-DMASTER_WALLET_NAME={0}".format(config.MASTER_WALLET_NAME),
        "-DCLEOS_EXECUTABLE={0}".format(config.CLEOS_EXECUTABLE),
        "-DKEOSD_EXECUTABLE={0}".format(config.KEOSD_EXECUTABLE),
        "-DKEOSD_CERTIFICATE_CHAIN_FILE={0}".format(config.KEOSD_CERTIFICATE_CHAIN_FILE),
        "-DKEOSD_PRIVATE_KEY_FILE={0}".format(config.KEOSD_PRIVATE_KEY_FILE),
        "-DKEOSD_IP_ADDRESS={0}".format(config.KEOSD_IP_ADDRESS),
        "-DKEOSD_PORT={0}".format(config.KEOSD_PORT),
        "-DNODEOS_WORKING_DIR={0}".format(config.NODEOS_WORKING_DIR),
        "-DNODEOS_IP_ADDRESS={0}".format(config.NODEOS_IP_ADDRESS),
        "-DNODEOS_PORT={0}".format(config.NODEOS_PORT),
        "-DNODEOS_EXECUTABLE={0}".format(config.NODEOS_EXECUTABLE),
        "-DPRODUCER_NAME={0}".format(config.PRODUCER_NAME),
        config.BEOS_DIR
    ]
    logger.info("Running cmake with params {0}".format(" ".join(params)))
    run_command(params, config.BEOS_BUILD_DIR)

    logger.info("Running make in {0}".format(config.BEOS_BUILD_DIR))
    params = ["make"]
    pcnt = get_processor_count()
    if pcnt > 1:
        params.append("-j{0}".format(pcnt))
    run_command(params, config.BEOS_BUILD_DIR)

def install_beos(c_compiler, cxx_compiler):
    install_eosio(c_compiler, cxx_compiler)

def build_beos(c_compiler, cxx_compiler):
    build_eosio(c_compiler, cxx_compiler)

def initialize_wallet():
    import eosio
    keosd = None
    logger.info("Starting initialize_wallet")
    try:
        wallet_url = "http://{0}:{1}".format(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT)
        eosio.run_keosd(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT, config.DEFAULT_WALLET_DIR, False, True)
        eosio.create_wallet(wallet_url, False)
        # import producer keys
        for producer, data in config.PRODUCERS_ARRAY.items():
            logger.info("Importing keys for producer: {0}".format(producer))
            eosio.import_key(config.MASTER_WALLET_NAME, data["prv_owner"], wallet_url)
            eosio.import_key(config.MASTER_WALLET_NAME, data["prv_active"], wallet_url)

        return keosd
    except Exception as ex:
        eosio.terminate_running_tasks(None, keosd)
        logger.error("Exception during initialize_wallet: {0}".format(ex))
        raise

def initialize_beos():
    import eosio
    keosd = None
    nodeos = None
    try:
        keosd = initialize_wallet()
        nodeos = eosio.run_nodeos(config.START_NODE_INDEX, config.PRODUCER_NAME, config.EOSIO_PUBLIC_KEY)

        eosio_actions.create_account("eosio", "eosio.msig", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio_actions.create_account("eosio", "eosio.names", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio_actions.create_account("eosio", "eosio.saving", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio_actions.create_account("eosio", "eosio.vpay", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio_actions.create_account("eosio", "eosio.unregd", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)

        eosio_actions.create_account("eosio", "eosio.bpay", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)

        eosio_actions.create_account("eosio", "eosio.ram", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio_actions.create_account("eosio", "eosio.ramfee", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio_actions.create_account("eosio", "eosio.stake", config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)

        eosio.create_account("eosio", "eosio.token", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_ACTIVE_PUBLIC_KEY)
        eosio.create_account("eosio", "beos.init", config.EOSIO_PUBLIC_KEY, config.COMMON_SYSTEM_ACCOUNT_OWNER_PUBLIC_KEY)

        eosio_actions.create_account("eosio", "producerjson", config.PRODUCERJSON_OWNER_PUBLIC_KEY, config.PRODUCERJSON_ACTIVE_PUBLIC_KEY)
        eosio_actions.create_account("eosio", "regproxyinfo", config.REGPROXYINFO_OWNER_PUBLIC_KEY, config.REGPROXYINFO_ACTIVE_PUBLIC_KEY)

        # create producer accounts
        for producer, data in config.PRODUCERS_ARRAY.items():
            logger.info("Creating producer account for: {0}".format(producer))
            eosio.create_account("eosio", producer, data["pub_owner"], data["pub_active"])

        eosio_actions.set_contract("eosio.token", config.CONTRACTS_DIR + "/eosio.token", "eosio.token")

        eosio.push_action("eosio.token", "create", '[ "eosio", "{0}"]'.format(config.CORE_TOTAL_SUPPLY), "eosio.token")
        eosio.push_action("eosio.token", "create", '[ "beos.gateway", "{0}"]'.format(config.PXBTS_TOTAL_SUPPLY), "eosio.token")
        eosio.push_action("eosio.token", "create", '[ "beos.gateway", "{0}"]'.format(config.PXBRNP_TOTAL_SUPPLY), "eosio.token")
        eosio.push_action("eosio.token", "create", '[ "beos.gateway", "{0}"]'.format(config.PXEOS_TOTAL_SUPPLY), "eosio.token")

        # registering initial producers, regproducer is in eosio.system contract so it need to be loaded first
        eosio.set_contract("eosio", config.CONTRACTS_DIR + "eosio.system", "eosio")
        time.sleep(2)
        eosio.set_contract("beos.init", config.CONTRACTS_DIR + "eosio.init", "beos.init")
        eosio.set_contract("beos.gateway", config.CONTRACTS_DIR + "eosio.gateway", "beos.gateway")
        eosio.set_contract("beos.distrib", config.CONTRACTS_DIR + "eosio.distribution", "beos.distrib")
        time.sleep(2)
        eosio.set_contract("producerjson", config.CONTRACTS_DIR + "producerjson", "producerjson")
        eosio.set_contract("regproxyinfo", config.CONTRACTS_DIR + "proxyinfo", "regproxyinfo")

        eosio_actions.push_action("eosio", "initialissue", '[ "{0}", "{1}" ]'.format(config.CORE_INITIAL_SUPPLY, config.MIN_ACTIVATED_STAKE_PERCENT), "eosio")
        eosio_actions.push_action("eosio", "initresource", '[ "beos.gateway", "{0}", "{1}", "{2}"]'.format(config.GATEWAY_INIT_RAM, config.GATEWAY_INIT_NET, config.GATEWAY_INIT_CPU), "eosio")
        # eosio.get_account("eosio")
        # eosio.get_account("beos.gateway")
        eosio_actions.push_action("eosio", "initresource", '[ "beos.distrib", "{0}", "-1", "-1"]'.format(config.DISTRIB_INIT_RAM), "eosio")
        # eosio.get_account("eosio")
        # eosio.get_account("beos.distrib")
        balance = eosio_actions.get_balance("eosio", config.CORE_SYMBOL_NAME)
        balance_int = int(balance * (10 ** config.CORE_SYMBOL_PRECISION) - config.DISTRIB_NETCPU_LEFTOVER)
        # all bandwidth resources to distribute must be stored as net! leftover value in cpu will also be subtracted from net reward pool
        eosio_actions.push_action("eosio", "initresource", '[ "beos.distrib", "-1", "{0}", "{1}"]'.format(balance_int, config.DISTRIB_NETCPU_LEFTOVER), "eosio")
        # eosio.get_account("eosio")
        # eosio.get_account("beos.distrib")
        eosio.push_action("beos.init", "storeparams", '[0]', "beos.init")
        import json
        eosio.push_action("beos.distrib", "changeparams", '{{"new_params": {0}}}'.format(json.dumps(config.DISTRIBUTION_PARAMS)), "beos.distrib")
        eosio.push_action("beos.gateway", "changeparams", '{{"new_params": {0}}}'.format(json.dumps(config.GATEWAY_PARAMS)), "beos.gateway")

        producers = []

        if len(config.PRODUCERS_ARRAY) == 0:
            # special case, register eosio as producer but only if it is defined as single one.
            producers.append({"producer_name": config.PRODUCER_NAME, "block_signing_key": config.EOSIO_PUBLIC_KEY})
            eosio.push_action("eosio", "regproducer", '["{0}", "{1}", "{2}", 0]'.format(config.PRODUCER_NAME, config.EOSIO_PUBLIC_KEY, "http://dummy.net"), config.PRODUCER_NAME)

        for producer, data in config.PRODUCERS_ARRAY.items():
            logger.info("Registering producer account for: {0}".format(producer))
            eosio.push_action("eosio", "regproducer", '["{0}", "{1}", "{2}", 0]'.format(producer, data["pub_active"], data["url"]), producer)

        for producer, data in config.PRODUCERS_ARRAY.items():
            producers.append({"producer_name": producer, "block_signing_key": data["pub_active"]})
        args = {"schedule" : producers}
        # set initial producers, setprods is in eosio.bios contract so we need to load it first
        logger.info("Setting initial producers via setprods: '{0}'".format(json.dumps(args)))
        eosio.push_action("eosio", "defineprods", '{0}'.format(json.dumps(args)), "eosio")

        eosio.create_account("beos.gateway", "beos.trustee", config.TRUSTEE_OWNER_PUBLIC_KEY, config.TRUSTEE_ACTIVE_PUBLIC_KEY, True)

        #Just to produce few blocks and accept lately scheduled transaction(s)
        # we will wait for approx 10 blocks to be produced
        eosio_tools.wait_for_blocks_produced(10, config.NODEOS_IP_ADDRESS, config.NODEOS_PORT)
        eosio_runner.terminate_running_tasks()
        eosio_runner.show_keosd_postconf(config.KEOSD_IP_ADDRESS, config.KEOSD_PORT, config.DEFAULT_WALLET_DIR)
        eosio_runner.show_wallet_unlock_postconf()
        eosio_runner.show_nodeos_postconf(config.START_NODE_INDEX, config.PRODUCER_NAME, config.EOSIO_PUBLIC_KEY)
    except Exception as ex:
        eosio_runner.terminate_running_tasks()
        logger.error("Exception during initialize: {0}".format(ex))
        raise
        #sys.exit(1)

def clear_initialization_data(node_index, name):
    from shutil import rmtree
    if os.path.exists(config.DEFAULT_WALLET_DIR):
        logger.info("{0} exists. Deleting.".format(config.DEFAULT_WALLET_DIR))
        rmtree(config.DEFAULT_WALLET_DIR)

    if os.path.exists(config.WALLET_PASSWORD_DIR):
        logger.info("{0} exists. Deleting.".format(config.WALLET_PASSWORD_DIR))
        rmtree(config.WALLET_PASSWORD_DIR)

    working_dir = "{0}{1}-{2}/".format(config.NODEOS_WORKING_DIR, node_index, name)
    if os.path.exists(working_dir):
        logger.info("{0} exists. Deleting.".format(working_dir))
        rmtree(working_dir)

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
    run_command(params, tests_working_dir)

def make_beos_plugin_test():
    logger.info("Running BEOS plugin tests")
    tests_working_dir = "{0}/{1}".format(config.BEOS_BUILD_DIR, "tests/beos_plugin_tests/")

    params = ["./test03.py", "--main-dir", config.BEOS_BUILD_DIR]
    run_command(params, tests_working_dir)

    params = ["./test05_account_creation_with_delegate_ram.py", "--main-dir", config.BEOS_BUILD_DIR, "--ip-address", config.NODEOS_IP_ADDRESS, '--port', str(config.NODEOS_PORT)]
    run_command(params, tests_working_dir)

if __name__ == '__main__':
    from optparse import OptionParser, OptionGroup
    parser = OptionParser(usage = "Usage: %prog options")

    generalGroup = OptionGroup(parser, "General actions")
    generalGroup.add_option("--c-compiler", action="store", type="string", default=config.DEFAULT_C_COMPILER, dest="c_compiler", help="Set C compiler")
    generalGroup.add_option("--cxx-compiler", action="store", type="string", default=config.DEFAULT_CXX_COMPILER, dest="cxx_compiler", help="Set CXX compiler")

    librariesGroup = OptionGroup(parser, "Libraries and system requirements actions")
    librariesGroup.add_option("--install-system-packages", action="store_true", dest="install_system_packages", help="Install system packages available in system repositories.")
    librariesGroup.add_option("--install-boost", action="store_true", dest="install_boost", help="Install newest version of the boost library.")
    librariesGroup.add_option("--install-mongo-driver", action="store_true", dest="install_mongo_driver", help="Install C and C++ drivers for MongoDB.")
    librariesGroup.add_option("--install-wasm", action="store_true", dest="install_wasm", help="Install WASM compiler.")
    librariesGroup.add_option("--install-libraries", action="store_true", dest="install_libraries", help="Install boost, mongo plugin and WASM compiler in one step.")

    buildGroup = OptionGroup(parser, "BEOS/EOSIO building and installing actions")
    buildGroup.add_option("--install-eosio", action="store_true", dest="install_eosio", help="Build EOSIO and install it to the specified directory.")
    buildGroup.add_option("--build-eosio", action="store_true", dest="build_eosio", help="Build EOSIO without installing.")

    buildGroup.add_option("--install-all", action="store_true", dest="install_all", help="Install all required packages, build EOSIO with BEOS and install it to specyfied path")
    buildGroup.add_option("--install-beos", action="store_true", dest="install_beos", help="Build EOSIO with BEOS and install it to specyfied path")
    buildGroup.add_option("--build-beos", action="store_true", dest="build_beos", help="Build EOSIO with BEOS without installing")

    postinstallGroup = OptionGroup(parser, "Postinstallation actions")
    postinstallGroup.add_option("--clear-initialization-data", action="store_true", dest="clear_init_data", help="Removes all data set in initialization process!")
    
    postinstallGroup.add_option("--initialize-wallet", action="store_true", dest="initialize_wallet", help="")
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

    c_compiler = options.c_compiler
    cxx_compiler = options.cxx_compiler

    if options.install_system_packages:
        install_system_packages()

    if options.install_boost:
        install_boost()

    if options.install_mongo_driver:
        install_mongo_driver()

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

    if options.clear_init_data:
        clear_initialization_data(config.START_NODE_INDEX, "eosio")

    if options.initialize_beos:
        initialize_beos()

    if options.initialize_wallet:
      initialize_wallet()

    # close loggers
    config.log_main.close()
    config.log_error.close()
