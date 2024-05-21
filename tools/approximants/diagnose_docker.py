import os
from configparser import ConfigParser

import docker
from pathlib import Path


# setup the container
client = docker.from_env()
# output = os.getcwd()+'/output'
# if not os.path.isdir(output): os.makedirs(output)
volumes = {os.getcwd(): {'bind': '/input', 'mode': 'ro'}} # output: {'bind': '/output', 'mode': 'rw'}
commands = ['cp /input/diagnose_approximants.py /']
script = 'python diagnose_approximants.py'

# run the container
container = client.containers.run("mdaamkit/mpi", detach=True, tty=True, volumes=volumes)
	# tty=True is necessary to keep the container running even if it has no jobs to do.
	# remove=True could be used to auto-remove the container after it has finished running.
for command in commands:
	container.exec_run(command)
std = container.exec_run(script, demux=True)
container.stop()
client.containers.prune()

# output results
lines = std.output[0].decode('UTF-8').splitlines()
for line in lines:
	print(line)
with open('diagnose_docker_output.txt', 'w') as file:
	for line in lines:
		file.write(line+'\n')