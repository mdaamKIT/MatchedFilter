#!/usr/bin/python3

# This file seeks to handle communication between the templatebank_handler and mics_pycbc_interface.
# Communication needs to be handled a little differently depending on operation system (linux or windows) as pycbc is not available on Windows.
# If running on a windows machine, mics_pycbc_interface has to be exiled in a docker container.
# All complexity added by the distinction between communicating directly (linux) and to a script running in a container (windows) is outsourced into this file.


OS = 'win'   # I guess I should get this from a config-file later


import docker

# setup a client and run a container
client = docker.from_env()
volumes = {'/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/docker/d01_setup-ctm/': {'bind': '/output', 'mode': 'rw'}}
container = client.containers.run("mdaamkit/mpi", detach=True, tty=True, volumes=volumes) # tty=True ist notwendig, damit der Container am Laufen bleibt, auch wenn er keinen Job hat.

# test if it works
# container.exec_run("touch /output/testfile3.txt") # works
# container.exec_run('''python -c 'import numpy as np; np.savetxt("/output/NowAbleToRunNumpyInContainer.txt", np.arange(10))' ''') # works
container.exec_run('''python -c 'import os; print(os.getcwd(), file=open("/output/WorkingDirectory.txt", "w"))' ''')
# container.exec_run('''python -c 'import os; print(os.listdir(), file=open("/output/ListOfDirectory.txt", "w"))' ''') # works
container.exec_run('''python -c 'import os; print(os.listdir("/"), file=open("/output/ListOfOutput.txt", "w"))' ''')
container.exec_run('''python test_writing_files.py''') # this did not work, but as the next line did, I guess I don't need that anyway.
container.exec_run('''python -c 'import mics_pycbc_interface as mpi; mpi.makefile("/output/NowAbleToRunMpiInContainer.txt")' ''')   # https://stackoverflow.com/questions/18616252/python-nest-more-than-two-types-of-quotes
container.stop()

# this works so far.