#!/usr/bin/env python3

<<<<<<< HEAD
=======
def usage():
    print("Wait for process PID to close")
    print("wait.py pid")

>>>>>>> Sigint instead of sigterm in run.py. Wait.py helper script
if __name__ == "__main__":
    import os
    import sys
    import time
    argc = len(sys.argv)

    if argc == 2:
        try:
            pid = int(sys.argv[1])
            tries = 10000 # infinite lock protection
            while tries > 0:
<<<<<<< HEAD
<<<<<<< HEAD
                time.sleep(0.5)
=======
                time.sleep(1)
>>>>>>> Sigint instead of sigterm in run.py. Wait.py helper script
=======
                time.sleep(0.5)
>>>>>>> Waiting time reduced to 0.5 sec per iteration
                try:
                    os.kill(pid, 0) 
                except ProcessLookupError: # errno.ESRCH
                    break
                except PermissionError: # errno.EPERM
                    pass
                else:
                    pass
                tries = tries - 1
        except Exception as ex:
            print("Error running script: {0}".format(ex))
            sys.exit(1)
<<<<<<< HEAD
=======
    else:
        usage()
        sys.exit(1)
>>>>>>> Sigint instead of sigterm in run.py. Wait.py helper script
