import six
import subprocess

from beos_test_utils.logger        import log
from beos_test_utils.eoscallerbase import EOSCallerBase

class CleosCallerException(Exception):
    def __init__(self, _message):
        self.message = _message

    def __str__(self):
        return self.message


class EOSCleosCaller(EOSCallerBase):
    def __init__(self, _node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name, _path_to_cleos):
        super(EOSCleosCaller, self).__init__(_node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name)

        self.path_to_cleos = _path_to_cleos
        if self.path_to_cleos != None and self.path_to_cleos.endswith('/'):
            self.path_to_cleos = self.path_to_cleos+"cleos"

    def make_call(self, _parameters):
        try:
            log.info("Cleos call parameters {0}".format(_parameters))
            parameters = []
            if isinstance(_parameters, six.string_types):
                parameters = _parameters.split()
            elif isinstance(_parameters, dict):
                for key, value in _parameters.items():
                    parameters.append(key)
                    parameters.append(value)
            elif isinstance(_parameters, list):
                parameters = _parameters
            else:
                raise CleosCallerException("Invalid `parameters` type {0}".format(type(_parameters)))
            parameters.insert(0, self.path_to_cleos)
            print(parameters)
            ret = subprocess.run(parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            retcode = ret.returncode
            log.info("Cleos retcode {0}".format(retcode))
# Sometimes retcode >0 is a good result that we want.
#            if retcode > 0:
#                raise CleosCallerException("Faild to execute cleos call with `{0}` parameters.".format(parameters))
            if retcode > 0:
                return ret.stderr.decode('utf-8')
            return ret.stdout.decode('utf-8')
        except Exception as _ex:
            log.exception("Exception `{0}` occures while preparing cleos call.".format(str(_ex)))