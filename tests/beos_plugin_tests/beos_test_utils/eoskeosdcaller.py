import subprocess

from beos_test_utils.eoscallerbase import EOSCallerBase

class EOSKeosdCaller(EOSCallerBase):
    def __init__(self, _node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name, _path_to_keosd):
        super(EOSKeosdCaller, self).__init__(_node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name)

        self.path_to_keosd = _path_to_keosd

    def make_call(self, args):
        pass