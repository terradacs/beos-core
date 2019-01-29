import os
import sys	

from beos_test_utils.logger        import add_handler, log
from beos_test_utils.beosnode      import BEOSNode
from beos_test_utils.summarizer    import *
from beos_test_utils.cmdlineparser import parser

class BEOSUtilsException(Exception):
    def __init__(self, _message):
        self.message = _message

    def __str__(self):
        return "BEOSUtilsException exception `{0}`".format(self.message)

def init(_file):
    try:
        data = os.path.split(_file)
        cdir = data[0] if data[0] else "."
        cfile = data[1]
        args = parser.parse_args()
        node = BEOSNode(args.nodeos_ip, args.nodeos_port, args.keosd_ip,
            args.keosd_port, args.master_wallet_name, args.path_to_cleos)
        node.set_node_dirs(cdir+"/node/"+cfile, cdir+"/logs/"+cfile)
        summary = Summarizer(cdir+"/"+cfile)
        add_handler(cdir+"/logs/"+ cfile+"/"+cfile)

        return node, summary, args, log
    except Exception as _ex:
        raise BEOSUtilsException(str(_ex))
