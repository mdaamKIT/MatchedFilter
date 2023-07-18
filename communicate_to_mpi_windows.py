#!/usr/bin/python3


# This file seeks to handle communication between the templatebank_handler and mics_pycbc_interface.
# It operates on the host, commanding a docker container.
# Communication needs to be handled a little differently depending on operation system (linux or windows) as pycbc is not available on Windows.
# If running on a windows machine, mics_pycbc_interface has to be exiled into a docker container.
# All complexity added by communicating to a script running in a container (windows) is handled by this file.


### How the container works:
#   ------------------------
#   - Configure all the directories with files in them to be read by the container or where files should be written by it.
#       These configurations get written into the MPIConnection.volumes dictionary.
#       They can not be changed, once the container is started.
#   - Collect all the code that should be executed inside the container.
#       This code consists of two parts:
#         * A list of commands than can be executed one after the other, preparing the container for the final python script.
#         * A python 'script' to be run in the container. 
#             It has to be run in one go since e.g. the template-object has to stick inside the cache until the matched filtering is done.
#   - Run the container (MPIConnection.run()) with the pre-setup configurations, executing the commands from the commands list and the python script.
#       At the end of the run() function, the container will be stopped and deleted and the MPIConnection variables are set back to their initial values.
#       Now you could start again, configuring the container.


debugmode = True

import docker

class MPIConnection:
	def __init__(self):
		self.client = docker.from_env()
		self.volumes = {}     # {output_host: {'bind': output_container, 'mode': 'rw'}}
		self.commands = []
		self.script = '''python -c 'import mics_pycbc_interface as mpi; '''
		
	def add_output_dir(self, output_host, output_container):
		'Bind-mounts a directory from host to the container to (read and) write files into.'
		self.volumes[output_host] = {'bind': output_container, 'mode': 'rw'}

	def add_read_dir(self, input_host, input_container):
		'Bind-mounts a directory from host for the container to read files from.'
		self.volumes[input_host] = {'bind': input_container, 'mode': 'ro'}

	###### !!!!! Note: first, I used the shortnames of the files as identifiers for the objects. That did not work, as they contained hyphens ('-') which are not allowd in names in python.

	def transfer_data(self, data):
		'Transfer a Data object from the templatebank_handler to mics_pycbc_interface inside the container.'
		datapath_container = '/input/'+data.shortname+'/'
		savepath_container = '/output/'+data.shortname+'/'
		self.add_read_dir(data.datapath, datapath_container)
		self.add_output_dir(data.savepath, savepath_container)
		self.script += 'data = mpi.Data("'+self.volumes[data.datapath]['bind']+'","'+data.filename+'","'+self.volumes[data.savepath]['bind']+'",'+str(data.preferred_samplerate)+','+str(data.segment_duration)+','+str(data.flag_show)+'); '

	def transfer_template(self, template):
		'Transfer a Template object from the templatebank_handler to mics_pycbc_interface inside the container.'
		templatepath_container = '/input/templates/'+template.shortname+'/'
		self.add_read_dir(template.bankpath, templatepath_container)
		self.script += 'template = mpi.Template("'+self.volumes[template.bankpath]['bind']+'","'+template.filename+'"); '

	def matched_filter(self):
		'Perform Matched Filtering inside the container.'
		self.script += 'mpi.do_matched_filter( data, template ); '

	### running and stopping the container

	def run(self):
		'Running the prepared commands and script inside the container and clearing them.'
		# start container
		container = self.client.containers.run("mdaamkit/mpi", detach=True, tty=True, volumes=self.volumes) # tty=True is necessary to keep the container running even if it has no jobs to do.
		# run code in container
		for command in self.commands:
			container.exec_run(command)
		self.script += ''' ' '''
		std_stuff = container.exec_run(self.script, demux=True)
		if debugmode: print(std_stuff)
		# stop container and cleanup (prepare for restart)
		container.stop()
		self.client.containers.prune()
		self.volumes = {}
		self.commands = []
		self.script = '''python -c 'import mics_pycbc_interface as mpi; '''

	def update_mpi(self, path_host, path_container):
		'Update mpi without building a new docker image.'
		self.add_read_dir(path_host, path_container)
		self.commands.append('cp '+path_container+'mics_pycbc_interface.py /')

	### finally composing everything (these method names are capitalized)
	#      only these methods need to be called from outside this script.

	def Matched_Filter(self, data, template):
		'Composing a Matched Filtering with a single template.'
		self.transfer_data(data)
		self.transfer_template(template)
		self.matched_filter()
		self.run()


##### I have to make sure, flag_show is always False in windows!




### old snippets
#   ------------

# import os; print(os.listdir("/input/"), file=open("/output/ListOfInput.txt", "w")); 