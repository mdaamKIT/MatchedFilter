#!/usr/bin/python3

# This file seeks to handle communication between the templatebank_handler and mics_pycbc_interface.
# Communication needs to be handled a little differently depending on operation system (linux or windows) as pycbc is not available on Windows.
# If running on a windows machine, mics_pycbc_interface has to be exiled in a docker container.
# All complexity added by the distinction between communicating directly (linux) and to a script running in a container (windows) is outsourced into this file.


### I should make two files: one for communicating with mpi in the 

output_host = '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/docker/d02_testcommunicate/'
output_container = '/output/'


import docker
		
# setup a client and run a container
client = docker.from_env()
volumes = {output_host: {'bind': output_container, 'mode': 'rw'}}
container = client.containers.run("mdaamkit/mpi", detach=True, tty=True, volumes=volumes) # tty=True is necessary to keep the container running even if it has no jobs to do.



def mkdir_container(dirname):
'Creates the directory dirname inside output_container.'

	dirname = output_container+dirname

	if not os.path.isdir(dirname):
		os.makedirs(dirname)

	return



def stop_container(container):
	container.stop()



# # test if it works
# # container.exec_run("touch /output/testfile3.txt") # works
# # container.exec_run('''python -c 'import numpy as np; np.savetxt("/output/NowAbleToRunNumpyInContainer.txt", np.arange(10))' ''') # works
# container.exec_run('''python -c 'import os; print(os.getcwd(), file=open("/output/WorkingDirectory.txt", "w"))' ''')
# # container.exec_run('''python -c 'import os; print(os.listdir(), file=open("/output/ListOfDirectory.txt", "w"))' ''') # works
# container.exec_run('''python -c 'import os; print(os.listdir("/"), file=open("/output/ListOfOutput.txt", "w"))' ''')
# container.exec_run('''python test_writing_files.py''') # this did not work, but as the next line did, I guess I don't need that anyway.
# container.exec_run('''python -c 'import mics_pycbc_interface as mpi; mpi.makefile("/output/NowAbleToRunMpiInContainer.txt")' ''')   # https://stackoverflow.com/questions/18616252/python-nest-more-than-two-types-of-quotes
