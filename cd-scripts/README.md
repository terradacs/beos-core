# Continuous compilation, deployment and testing scripts for BEOS.

## Introduction
This set of deployment and testing scripts consist of three files:
- *deploy.py* - main executable file for continuous compilation, deployment and testing,
- *eosio.py* - helper library for creation system accounts, used by main executable,
- *config-example.py* - sample configuration file for main executable.
- *resources/config.ini* - template file for config.ini
- *

## Configuration
Before using scripts consider moving them outside clonde beos repository. If you set source clone dir as current beos dir all changes made in this dir could be removed when you call the script with
--download-sources option. So the configuration steps are:
1. (optional) Move cd-scripts directory to target location
2. Create configuration file: to do that make a copy of *config-example.py* and save it as *config.py*. 
3. Next, edit *config.py* file and set options to desired values:
    - set SOURCES_DOWNLOAD_DIR to a directory where source files should be downloaded.
    - set EOSIO_BUILD_DIR to a directory where build will be performed
    - set EOSIO_INSTALL_PREFIX to a directory where BEOS should be installed
    - set keys
For more informations about available build options please refer to *config.py* file.

Build procedure saves three log files. One in script root directory - for deploy.py operations, two in EOSIO_BUILD_DIR.

*Note:* Nodeos and keosd default http interfaces addresses are set to localhost (127.0.0.1). Consider changing Nodeos http interface address to 0.0.0.0 for listening on all interfaces.

## Usage
### Script options
One can run *deploy.py* script with following options:
#### General actions:
- *--show-system-info* Shows system information.
- *--download-sources* Delete source tree and clone sources from git repository.

#### Libraries and system requirements actions:
- *--install-system-packages* Install system packages available in system repositories.
- *--install-boost* Install newest version of the boost library.
- *--install-mongo-driver* Install C and C++ drivers for MongoDB.
- *--install-wasm* Install WASM compiler.
- *--install-libraries* Install boost, mongo plugin and WASM compiler in one step.

#### BEOS/EOSIO building and installing actions:
- *--install-eosio* Build EOSIO and install it to the specified directory.
- *--build-eosio* Build EOSIO without installing.
- *--install-all* Install all required packages, build EOSIO with BEOS and install it to specyfied path
- *--install-beos* Build EOSIO with BEOS and install it to specyfied path
- *--build-beos* Build EOSIO with BEOS without installing

#### Postinstallation actions:
- *--initialize-beos*   Runs executable and creates system accounts.
- *--create-genesis-and-config* Creates genesis.json and config.ini files.

#### Installation testing actions:
- *--make-integration-test* Run main EOSIO tests
- *--make-unit-test* Run suit of unit tests
- *--make-beos-plugin-test* Run BEOS plugin tests

### Usage scenarios
0. To print all available options run:
    `deploy.py`
    Deploy py requires some additional python libraries. Deploy.py will detect if given library is not installed and will print information on screen.
    
1. To install all system dependencies use:
    `deploy.py ----install-libraries --install-system-packages`

2. Build BEOS without installation:
    `deploy.py --download-sources --build-beos`

3. Rebuilding BEOS:
    `deploy.py --build-beos`

4. Build BEOS without installation with testing:
    `deploy.py --build-beos --make-unit-test --make-beos-plugin-test`

5. Initialize newly build BESO:
    `deploy.py --initialize-beos`
    After initialization follow instructions to run wallet service and newly configured node. Don't forget to unlock wallet.
