import json

def get_transaction_id_from_result(code, result):
  data = json.loads(result)
  return data["trx_id"]