import os
import logging
import datetime

log = None

class Logger(object):
    def __init__(self, _to_stdout):
        self.to_stdout = _to_stdout
        self.logger = logging.getLogger('myapp')
        self.hdlr = logging.FileHandler(os.getcwd()+"/"+"Scenarios_dump_"+str(datetime.datetime.now())[:-7])
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.hdlr.setFormatter(self.formatter)
        self.logger.addHandler(self.hdlr) 
        self.logger.setLevel(logging.INFO)
        

    def info(self, _message):
        self.log("[INFO]", _message)

    def warning(self, _message):
        self.log("[WARN]", _message)

    def error(self, _message):
        self.log("[ERRO]", _message)

    def log(self, _level, _message):
        if self.to_stdout:
            print(str(datetime.datetime.now())[:-3],_level,_message)

        if _level == "[INFO]":
            self.logger.info(_message)
        elif _level == "[WARN]":
            self.logger.warning(_message)
        elif _level == "[ERRO]":
            self.logger.error(_message)
        else:
            self.logger.info(_message)

if not log:
    log = Logger(True)