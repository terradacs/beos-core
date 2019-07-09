import subprocess

def run_command_and_return_output(parameters):
  ret = subprocess.run(parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  retcode = ret.returncode
  if retcode == 0:
    return (retcode, ret.stdout)
  else:
    return (retcode, ret.stderr)