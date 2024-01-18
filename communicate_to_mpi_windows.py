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

from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')
debugmode = config.getboolean('main', 'debugmode')

import docker
from pathlib import Path

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

	def transfer_templatebank(self, templatebank):
		'Transfer a TemplateBank object from the templatebank_handler to mics_pycbc_interface inside the container.'
		list_of_bankpaths_both = [(bankpath_host,'/input/templatebank/'+Path(bankpath_host).parts[-1]+'_'+str(distinction)+'/') for distinction, bankpath_host in enumerate(templatebank.list_of_bankpaths)]  # distinction because we really need unique names for different paths
		for bankpath_both in list_of_bankpaths_both:
			self.add_read_dir(bankpath_both[0], bankpath_both[1])
		self.script += 'templatebank = mpi.TemplateBank(); '
		for template in templatebank.list_of_templates:
			self.script += 'templatebank.add_template("'+self.volumes[template.bankpath]['bind']+'","'+template.filename+'"); '

	### !!!!! the following two methods could be integrated in the methods below (Matched_Filter_single/templatebank)

	def matched_filter_single(self):
		'Perform Matched Filtering inside the container.'
		self.script += 'mpi.matched_filter_single( data, template ); '

	def matched_filter_templatebank(self):
		self.script += 'mpi.matched_filter_templatebank( data, templatebank ); '



	### running and stopping the container

	def run(self):
		'Running the prepared commands and script inside the container and clearing them.'
		# start container
		container = self.client.containers.run("mdaamkit/mpi", detach=True, tty=True, volumes=self.volumes) 
			# tty=True is necessary to keep the container running even if it has no jobs to do.
			# remove=True could be used to auto-remove the container after it has finished running
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

	def Matched_Filter_single(self, data, template):
		'Composing a Matched Filtering with a single template.'
		self.transfer_data(data)
		self.transfer_template(template)
		self.matched_filter_single()
		self.run()

	def Matched_Filter_templatebank(self, data, templatebank):
		'Composing a Matched Filtering with every template in the templatebank.'
		self.transfer_data(data)
		self.transfer_templatebank(templatebank)
		self.matched_filter_templatebank()
		self.run()

	def Create_Templates(self, parameters, bankpath_host, basename, flag_Mr, freq_domain, time_domain):
		'Creates templates for further use in matched filtering (freq_domain) or as signals (time_domain).'
		# parameters should be a numpy array of dim 2xN; flag_Mr, freq_domain and time_domain should be boolean.
		# Hint: a seperate MPIConnection object should be called for creating these files to not interfere with the matched filtering.
		self.add_output_dir(bankpath_host, '/output')
		transfer_file = 'parameters.txt'
		parameters.tofile(bankpath_host+transfer_file)
		self.script += 'import numpy as np; '
		self.script += 'parameters = np.fromfile("/output/'+transfer_file+'").reshape((2,-1)); '
		self.script += 'mpi.create_templates(parameters, "/output/", "'+basename+'", '+str(flag_Mr)+', '+str(freq_domain)+', '+str(time_domain)+'); '
		self.run()


##### I have to make sure, flag_show is always False in windows!




### old snippets
#   ------------

# import os; print(os.listdir("/input/"), file=open("/output/ListOfInput.txt", "w")); 