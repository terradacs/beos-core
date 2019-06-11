

class EOSCallerBase(object):
    def __init__(self, _node_ip, _node_port, _keosd_ip, _keosd_port, _wallet_name, _using_https = False ):
        self.node_ip     = _node_ip.strip()
        self.node_port   = _node_port
        self.keosd_ip    = _keosd_ip.strip()
        self.keosd_port  = _keosd_port
        self.wallet_name = _wallet_name
        if _using_https:
            self.keosd_url  = "https://{0}:{1}".format(self.keosd_ip.s,self.keosd_port)
            self.nodeos_url = "https://{0}:{1}".format(self.node_ip,self.node_port)
        else:
            self.keosd_url  = "http://{0}:{1}".format(self.keosd_ip , self.keosd_port)
            self.nodeos_url = "http://{0}:{1}".format(self.node_ip  ,  self.node_port)
            
