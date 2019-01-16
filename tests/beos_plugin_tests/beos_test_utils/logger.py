import os
import sys
import logging
import datetime

log = logging.getLogger('beos_test_utils')
formater = '%(asctime)s [%(levelname)s] %(message)s'
stdh = logging.StreamHandler(sys.stdout)
stdh.setFormatter(logging.Formatter(formater))
log.addHandler(stdh)
log.setLevel(logging.INFO)

def add_handler(_file_name):
    data = os.path.split(_file_name)
    path = data[0] if data[0] else "./logs/"
    file = data[1]
    if path and not os.path.exists(path):
        os.makedirs(path)
    now = str(datetime.datetime.now())[:-7]
    now = now.replace(' ', '-')
    full_path = path+"/"+now+"_"+file
    if not full_path.endswith(".log"):
        full_path += (".log")
    fileh = logging.FileHandler(full_path)
    fileh.setFormatter(logging.Formatter(formater))
    log.addHandler(fileh)
