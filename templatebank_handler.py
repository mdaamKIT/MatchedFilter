#!/usr/bin/python3

import os
import glob
import numpy as np
import pycbc.types as types

### Select OS and establish a connection object to communicate to mpi


OS = 'windows'   #  Either 'windows' or 'linux'. (In fact, either 'windows' or something else. I guess on a mac this might work as if linux, but I was not able/willing hard enough to test.)
if OS == 'windows':
	import communicate_to_mpi_windows as ctm
else:
	import communicate_to_mpi_linux as ctm



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
	
	def add_template(self, bankpath, filename):
		'Add a single file to the TemplateBank.'
		self.list_of_templates.append(Template(bankpath, filename))
		print('Added ', self.list_of_templates[-1].shortname, ' to the TemplateBank.')
	
	def add_directory(self, path):
		'Add all .hdf-files in path to the TemplateBank.'
		listofnames = [f for f in os.listdir(path) if f.endswith('.hdf')]
		listofnames.sort()
		for filename in listofnames:
			self.add_template(path, filename)

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
		self.savepath = self.datapath+'/'+self.shortname
		# Some settings are fixed so far. They can be changed with explicitly calling their changing methods (see below) but there should be no need.
		self.flag_show = False
		self.preferred_samplerate = 4096
		self.segment_duration = 1
		# self.ending = '.wav'

	def matched_filter_single(self, template, connection):   # it feels a little ugly, to use a connection that is not really defined inside here. (It has to be a ctm.MPIConnection object and gets called from matchedfilter.py via the connect-method at the bottom of this file.)
		'Tries to find a single template in the data.'
		if not isinstance(template, Template):
			raise TypeError('template has to be an instance of Template class but has type: ' + str(type(template)))
		
		connection.Matched_Filter(self, template)




		### this has to be broken!
		# but I save it to keep how results were returned previously
		# def matched_filter(template, data)
		# 	_,_,_,Maxmatch = do_matched_filter(template.frequency_series, data_segments, template.shortname, self.shortname, self.savepath, Data.flag_show)
		# 	print()
		# 	print('Matched filtering of '+self.shortname+' with '+template.shortname+': ')
		# 	print(Maxmatch[0],' at ',Maxmatch[1],' sec.')


	def matched_filter_templatebank(self, templatebank):
		'Checks the data for all templates in the template bank.'
		if not isinstance(templatebank, TemplateBank):
			raise TypeError('templatebank has to be an instance of TemplateBank class but has type: ' + str(type(templatebank)))
		dtype = [('templatename', (np.str_,40)), ('maxmatch', np.float64), ('maxtime', np.float64)]
		writedata = np.array(np.arange(len(templatebank.list_of_templates)), dtype=dtype)
		# calculate
		for index,template in enumerate(templatebank.list_of_templates):
			template_freqseries = types.frequencyseries.load_frequencyseries(template.bankpath+template.filename)
			_,_,_,Maxmatch = mpi.do_matched_filter(template_freqseries, self.data_segments, template.shortname, self.shortname, self.savepath, Data.flag_show)
			writedata[index] = template.shortname, Maxmatch[0], Maxmatch[1]
		# save statistics
		header = 'Matched Filteting results of '+self.shortname+': \n'
		header += 'templatename, match, time of match'
		np.savetxt(self.savepath+'00_matched_filtering_results.dat', writedata, fmt=['%s', '%f', '%f'], header=header)


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

def connect():
	connection = ctm.MPIConnection()
	return connection