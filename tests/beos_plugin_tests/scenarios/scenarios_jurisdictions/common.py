def get_transaction_id_from_result(code, result):
  import re
  ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
  result_str = ansi_escape.sub('', result)

  result_str = result_str.strip().split("\n")
  if code == 0:
    return str(result_str[0].strip().split(" ")[2].strip())
  else:
    return str(result_str[-1].strip().split(" ")[-1].strip())