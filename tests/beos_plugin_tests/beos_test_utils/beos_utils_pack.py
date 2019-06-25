import os
import sys
import socket	

from beos_test_utils.logger        import add_handler, log
from beos_test_utils.beosnode      import BEOSNode
from beos_test_utils.summarizer    import *
from beos_test_utils.cmdlineparser import parser
from beos_test_utils.cluster       import Cluster


class BEOSUtilsException(Exception):
    def __init__(self, _message):
        self.message = _message

    def __str__(self):
        return "BEOSUtilsException exception `{0}`".format(self.message)

def init(_file, _bios = False):
    try:
        data = os.path.split(_file)
        cdir = data[0] if data[0] else "."
        cfile = data[1]
        args = parser.parse_args()
        node = BEOSNode(args.nodeos_ip, args.nodeos_port, args.keosd_ip,
            args.keosd_port, args.master_wallet_name, args.path_to_cleos)
        node.set_node_dirs(cdir+"/node/"+cfile, cdir+"/logs/"+cfile, _new_dir = _bios)
        summary = Summarizer(cdir+"/"+cfile)
        add_handler(cdir+"/logs/"+ cfile+"/"+cfile)

        return node, summary, args, log
    except Exception as _ex:
        raise BEOSUtilsException(str(_ex))

def init_cluster(_file, _pnodes, _producers_per_node):
    bios_node, summary, args, log = init(_file, True)
    log_handlers = log.handlers
    cluster = Cluster(bios_node, _pnodes, _producers_per_node, _file)
    cluster.initialize_bios()
    log.handlers = log_handlers
    return cluster, summary, args, log
