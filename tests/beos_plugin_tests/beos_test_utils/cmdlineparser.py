import argparse

parser = None

if not parser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--nodeos-ip', metavar='', help="Ip address of nodeos ", default='127.0.0.1', dest="nodeos_ip")
    parser.add_argument('--keosd-ip', metavar='', help="Ip address of keosd", default='127.0.0.1', dest="keosd_ip")
    parser.add_argument('--nodeos-port', metavar='', help="Port", default='8888')
    parser.add_argument('--keosd-port', metavar='', help="Port", default='8900')
    parser.add_argument('--master-wallet-name', metavar='', help="Name of main wallet.", default="beos_master_wallet" )
    parser.add_argument('--path-to-cleos', metavar='', help="Path to cleos executable." )
    parser.add_argument('--path-to-contracts', metavar='', help="Path to contracts dir." )
    parser.add_argument('--scenarios', metavar='', help="Path to scenario(s) *.py file(s)." )
    parser.add_argument('--position-reporter-path', dest="position_reporter_path")
    parser.add_argument('--force-seed')
