#!/usr/bin/python3

import json
import logging
import sys

MODULE_NAME = "Convert ISO3166 countries to BEOS jurisdictions json format"
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
MAIN_LOG_PATH = './import_iso3166_countries.log'

logger = logging.getLogger(MODULE_NAME)
logger.setLevel(LOG_LEVEL)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(LOG_LEVEL)
ch.setFormatter(logging.Formatter(LOG_FORMAT))

fh = logging.FileHandler(MAIN_LOG_PATH)
fh.setLevel(LOG_LEVEL)
fh.setFormatter(logging.Formatter(LOG_FORMAT))

logger.addHandler(ch)
logger.addHandler(fh)

class Jurisdiction:
  def __init__(self, code, name, description):
    self.code = code
    self.name = name
    self.description = description

class JurisdictionJSONEncoder(json.JSONEncoder):
  def default(self, obj):
      if isinstance(obj, Jurisdiction):
          return dict(code = obj.code, name = obj.name, description = obj.description)
      # Let the base class default method raise the TypeError
      return json.JSONEncoder.default(self, obj)

if __name__ == "__main__":
  import argparse

  try:
    import pycountry
  except Exception as ex:
    print('Please install pycountry module i.e. pip install pycountry')

  parser = argparse.ArgumentParser()
  parser.add_argument('--out_file', type=str, const="iso3166_jurisdictions.json", default="iso3166_jurisdictions.json", nargs='?', help="Pathname to the output JSON file to be produced")
  args = parser.parse_args()

  try:
    with open(args.out_file, mode="w+t", encoding="utf-8") as f:

      jurisdiction_list = list()

      for c in pycountry.countries:
        jurisdiction_list.append(Jurisdiction(c.numeric, c.name, c.official_name if hasattr(c, 'official_name') else c.name))

      json.dump(fp=f, obj=dict(default=jurisdiction_list), cls=JurisdictionJSONEncoder, sort_keys=True, ensure_ascii = False, indent=2)

  except Exception as ex:
    logger.error("Error during conversion {}".format(ex))
