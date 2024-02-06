#!/usr/bin/python3

import os
import glob
import numpy as np
# from configparser import ConfigParser

### Get OS from config.ini and establish a connection object to communicate to mpi

# config = ConfigParser()
# config.read('config.ini')
# OS = config.get('main', 'OS')

### maybe it is better to import both and decide upon establishing a connection, from which a connection should be established?

import communicate_to_mpi_windows as ctm
## import communicate_to_mpi_linux as ctm  # maybe I can really directly import mpi? I guess, I need to create another file, communicating

### !!!! maybe I could import communicate_to_mpi_windows as mpi for windows and mpi as mpi for linux?
#         Maybe this is a bad idea, as I need the connection-object stable? Can it just be created (and destroyed) by calling a mpi-function



### About the templatebank_handler and mics_pycbc_interface
#   -------------------------------------------------------

# This file should be outside the container, while mics_pycbc_interface has to be inside.
# The templatebank_handler (handler) contains the classes handling the matched filtering 
# while mics_pycbc_interface (mpi) deals with all the details about converting filetypes, samplerates, segmentation, ...
# Everytime the templatebank_handler wants something concrete to be calculated, he calls functions from mpi.
# The templatebank_handler needs to run outside the container, as the container gets killed and setup newly multiple times
# without us wanting to lose track of already created instances of the classes in th.


### How this document is to be used  -  this info could be outdated!
#   -------------------------------

# This document contains the definition of two classes, Template and Data.
# They rely on some functions defined by me in the mpi-document.

# The classes are made to handle matched filtering between templates and data-signals.
# If you want to keep track of all your templates, initialize an empty TemplateBank and add the Templates to the TemplateBank via the TemplateBank.add_template method, don't use the constructer method of the Template-class directly then.
# Use add_directory method, if you want to add every hdf-file in a directory to the TemplateBank.


### Conventions
#   -----------

# Names ending with _container refer to paths, files, ... inside the container for OS=windows.
# Names ending with _host      refer to paths, files, ... on the host for OS=windows. For OS=linux the can even refer to the same path/file/... as _container. 

# templates should always be stored in a subdir of /input/ on container. Thus we assume, they are.

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
		connection = ctm.MPIConnection()    # We establish a parallel connection, to create templates independently and in between other commands on connection.
		connection.update_mpi(os.getcwd(), '/input/mpi/')   # remove or only execute in debugmode?
		list_old_templates = [f for f in os.listdir(bankpath) if f.endswith('.hdf')]
		connection.Create_Templates(array_masses, bankpath, basename, attribute, freq_domain, time_domain)
		list_new_templates = [f for f in os.listdir(bankpath) if f.endswith('.hdf') and f not in list_old_templates]
		for filename in list_new_templates: self.add_template(bankpath, filename, flag_print=False)
		print('Created '+str(len(array_masses[0]))+' templates and added them to the template bank.')


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

	def matched_filter(self, templatebank, OS, debugmode=False):
		'Performs Matched Filtering with every template in the templatebank.'
		if not isinstance(templatebank, TemplateBank):
			raise TypeError('templatebank has to be an instance of TemplateBank class but has type: ' + str(type(templatebank)))
		if OS == 'windows':
			connection = ctm.MPIConnection()
			if debugmode: connection.update_mpi(os.getcwd(), '/input/mpi/')
			connection.Matched_Filter_templatebank(self, templatebank)
		else:
			print('Error, linux style without docker not yet supported. Open config.ini, go to main and change os to windows.')

	### !!!!! I guess, the following ones are not needed and could be deleted.

	def set_datapath(self, newpath):
		self.datapath = newpath

	def set_shortname(self, newname):
		self.shortname = newname

	def set_savepath(self, newpath):
		self.savepath = newpath
		mkdir(self.savepath, relative=False)

	def clear(self):
		for file in glob.glob(self.savepath+self.shortname+'_*'):
			os.remove(file)


	# changing of presets (should never be necessary)

	def change_flagshow(self, new_flag):
		self.flag_show = new_flag

	def change_preferred_samplerate(self, new_samplerate):
		self.preferred_samplerate = new_samplerate

	def change_segment_duration(self, new_segment_duration):
		self.segment_duration = new_segment_duration

	def change_file_extension(self, new_file_extension):
		self.ending = new_file_extension



### Some additional helper functions
#   --------------------------------

def mkdir( dirname, relative=True ):
	'Creates the directory dirname.'

	if relative:
		cwd = os.getcwd()+'/'
		dirname = cwd+dirname

	if not os.path.isdir(dirname):
		os.makedirs(dirname)

	return

# def connect():
# 	connection = ctm.MPIConnection()
# 	return connection