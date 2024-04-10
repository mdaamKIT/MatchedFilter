import os
from configparser import ConfigParser

import docker
from pathlib import Path

config = ConfigParser()
config.read('config.ini')
debugmode = config.getboolean('main', 'debugmode')


### About the templatebank_handler and mics_pycbc_interface
#   -------------------------------------------------------

# The MatchedFilter software relies on functions of the pycbc package which is not available on Windows, but on linux and MacOS.
# To be working on Winodws machines as well, a docker container is used.
# Templatebank_handler_win manages the communication between the main application on the host (matchedfilter.py) 
# and the auxiliary interface for pycbc (mics_pycbc_interface, mpi) in the docker container. 


class TemplateBank:
	def __init__(self):
		self.list_of_templates = []
		self.list_of_bankpaths = []
	
	def add_template(self, bankpath, filename, flag_print=True):
		'Add a single file to the TemplateBank.'
		self.list_of_templates.append(Template(bankpath, filename))
		if not bankpath in self.list_of_bankpaths: self.list_of_bankpaths.append(bankpath)
		if flag_print: print('Added ', self.list_of_templates[-1].shortname, ' to the template bank.')
	
	def add_directory(self, path):
		'Add all .hdf-files in path to the TemplateBank.'
		listofnames = [f for f in os.listdir(path) if f.endswith('.hdf')]
		listofnames.sort()
		for filename in listofnames:
			self.add_template(path, filename, flag_print=False)
		print('Added all .hdf files in '+path+' to the template bank.')

	def create_templates(self, array_masses, bankpath, basename, attribute='individual', freq_domain=True, time_domain=False):
		'Creates templates and adds them to the templatebank.'
		connection = MPIConnection()
		if debugmode: connection.update_mpi()
		list_old_templates = [f for f in os.listdir(bankpath) if f.endswith('.hdf')]
		connection.Create_Templates(array_masses, bankpath, basename, attribute, freq_domain, time_domain)
		if freq_domain:
			list_new_templates = [f for f in os.listdir(bankpath) if f.endswith('.hdf') and f not in list_old_templates]
			for filename in list_new_templates: self.add_template(bankpath, filename, flag_print=False)
			print('Added '+str(len(list_new_templates))+' new templates to the template bank.')

class Template:
	def __init__(self, bankpath, filename):
		self.bankpath = bankpath
		self.filename = filename
		self.shortname = filename[:-4]
		
class Data:
	def __init__(self, datapath, filename):
		self.datapath = datapath
		self.filename = filename
		self.shortname = filename[:-4]
		self.savepath = self.datapath+self.shortname+'/'
		# Some settings are fixed so far. They can be changed with explicitly calling their changing methods (see below) but there should be no need.
		self.flag_show = False
		self.preferred_samplerate = 4096
		self.segment_duration = 1
		# self.ending = '.wav'

	def matched_filter(self, templatebank, debugmode=False):
		'Performs Matched Filtering with every template in the templatebank.'
		if not isinstance(templatebank, TemplateBank):
			raise TypeError('templatebank has to be an instance of TemplateBank class but has type: ' + str(type(templatebank)))
		mkdir(self.savepath, relative=False)
		connection = MPIConnection()
		if debugmode: connection.update_mpi()
		connection.Matched_Filter_templatebank(self, templatebank)

	def set_datapath(self, newpath):
		self.datapath = newpath

	def set_shortname(self, newname):
		self.shortname = newname

	def set_savepath(self, newpath):
		self.savepath = newpath
		mkdir(self.savepath, relative=False)

	# changing of presets (should never be necessary)

	def change_flagshow(self, new_flag):
		self.flag_show = new_flag

	def change_preferred_samplerate(self, new_samplerate):
		self.preferred_samplerate = new_samplerate

	def change_segment_duration(self, new_segment_duration):
		self.segment_duration = new_segment_duration

	def change_file_extension(self, new_file_extension):
		self.ending = new_file_extension



class MPIConnection:
	def __init__(self):
		self.client = docker.from_env()
		self.volumes = {}     # {output_host: {'bind': output_container, 'mode': 'rw'}}
		self.commands = []
		self.script = '''python -c 'import mics_pycbc_interface as mpi; '''
		self.add_read_dir(os.getcwd(), '/input/mf/')
		self.commands.append('cp /input/mf/config.ini /')
		
	def add_output_dir(self, output_host, output_container):
		'Bind-mounts a directory from host to the container to (read and) write files into.'
		self.volumes[output_host] = {'bind': output_container, 'mode': 'rw'}

	def add_read_dir(self, input_host, input_container):
		'Bind-mounts a directory from host for the container to read files from.'
		self.volumes[input_host] = {'bind': input_container, 'mode': 'ro'}

	def transfer_objects(self, data, templatebank):
		'Transfer a Data and a TemplateBank object from the templatebank_handler to mics_pycbc_interface inside the container.'
		# Data
		savepath_container = '/output/'+data.shortname+'/'
		self.add_output_dir(data.savepath, savepath_container)
		if data.datapath != data.savepath:
			datapath_container = '/input/'+data.shortname+'/'
			self.add_read_dir(data.datapath, datapath_container)
		self.script += 'data = mpi.Data("'+self.volumes[data.datapath]['bind']+'","'+data.filename+'","'+self.volumes[data.savepath]['bind']+'",'+str(data.preferred_samplerate)+','+str(data.segment_duration)+','+str(data.flag_show)+'); '
		# TemplateBank
		list_of_bankpaths = list(set(templatebank.list_of_bankpaths).difference([data.datapath, data.savepath]))
		list_of_bankpaths_both = [(bankpath_host,'/input/templatebank/'+Path(bankpath_host).parts[-1]+'_'+str(distinction)+'/') for distinction, bankpath_host in enumerate(list_of_bankpaths)]  # distinction because we really need unique names for different paths
		for bankpath_both in list_of_bankpaths_both:
			self.add_read_dir(bankpath_both[0], bankpath_both[1])
		self.script += 'templatebank = mpi.TemplateBank(); '
		for template in templatebank.list_of_templates:
			self.script += 'templatebank.add_template("'+self.volumes[template.bankpath]['bind']+'","'+template.filename+'"); '		

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
		std = container.exec_run(self.script, demux=True)
		if debugmode: print(std)
		# stop container and cleanup (prepare for restart)
		container.stop()
		self.client.containers.prune()
		self.volumes = {}
		self.commands = []
		self.script = '''python -c 'import mics_pycbc_interface as mpi; '''

	def update_mpi(self):
		'Update mpi without building a new docker image.'
		self.commands.append('cp /input/mf/mics_pycbc_interface.py /')


	### finally composing everything (these method names are capitalized)
	#      only these methods need to be called from outside this object.

	def Matched_Filter_templatebank(self, data, templatebank):
		'Composing a Matched Filtering with every template in the templatebank.'
		self.transfer_objects(data, templatebank)
		self.script += 'mpi.matched_filter_templatebank( data, templatebank ); '
		self.run()

	def Create_Templates(self, parameters, bankpath_host, basename, attribute, freq_domain, time_domain):
		'Creates templates for further use in matched filtering (freq_domain) or as signals (time_domain).'
		# parameters should be a numpy array of dim 2xN; flag_Mr, freq_domain and time_domain should be boolean.
		self.add_output_dir(bankpath_host, '/output')
		transfer_file = 'parameters.txt'
		parameters.tofile(bankpath_host+transfer_file)
		self.script += 'import numpy as np; '
		self.script += 'parameters = np.fromfile("/output/'+transfer_file+'").reshape((2,-1)); '
		self.script += 'mpi.create_templates(parameters, "/output/", "'+basename+'", "'+str(attribute)+'", '+str(freq_domain)+', '+str(time_domain)+'); '
		self.run()

##### I have to make sure, flag_show is always False in windows!



def mkdir( dirname, relative=True ):
	'Creates the directory dirname.'
	if relative:
		cwd = os.getcwd()+'/'
		dirname = cwd+dirname
	if not os.path.isdir(dirname):
		os.makedirs(dirname)
	return