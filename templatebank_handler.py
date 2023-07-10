#!/usr/bin/python3

import os
import glob
import numpy as np
import pycbc.types as types

import mics_pycbc_interface as mpi  # That one is selfmade and should be contained in the same dir than this file.


### How this document is to be used  -  this info could be outdated!
#   -------------------------------

# This document contains the definition of two classes, Template and Data.
# They rely on some functions defined by me in the mpi-document.

# The classes are made to handle matched filtering between templates and data-signals.
# If you want to keep track of all your templates, initialize an empty TemplateBank and add the Templates to the TemplateBank via the TemplateBank.add_template method, don't use the constructer method of the Template-class directly then.
# Use add_directory method, if you want to add every hdf-file in a directory to the TemplateBank.

class TemplateBank:
	def __init__(self):
		self.list_of_templates = []
	
	def add_template(self, bankpath, filename):
		'add a single file to the TemplateBank'
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
		self.shortname = filename[:-4]
		self.bankpath = bankpath
		self.filename = filename

class Data:

	# some settings that are global so far
	flag_show = False
	preferred_samplerate = 4096
	segment_duration = 1
	wav = '.wav'

	def __init__(self, datapath, filename):
		self.filename = filename
		self.setshortname(filename[:-4])
		self.setparentpath(datapath)
		self.data_segments = mpi.load_data(datapath+filename, self.preferred_samplerate, self.segment_duration)

	def check_template(self, template):
		'Tries to find the template in the data.'
		if not isinstance(template, Template):
			raise TypeError('template has to be an instance of Template class but has type: ' + str(type(template)))
		self.setsavepath()
		template_freqseries = types.frequencyseries.load_frequencyseries(template.bankpath+template.filename)
		_,_,_,Maxmatch = mpi.do_matched_filter(template_freqseries, self.data_segments, template.shortname, self.shortname, self.savepath, Data.flag_show)
		print()
		print('Matched filtering of '+self.shortname+' with '+template.shortname+': ')
		print(Maxmatch[0],' at ',Maxmatch[1],' sec.')

	def check_bank(self, templatebank):
		'Checks the data for all templates in the template bank.'
		if not isinstance(templatebank, TemplateBank):
			raise TypeError('templatebank has to be an instance of TemplateBank class but has type: ' + str(type(templatebank)))
		self.setsavepath()
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


	def setparentpath(self, newpath):
		self.parentpath = newpath

	def setshortname(self, newname):
		self.shortname = newname

	def setsavepath(self):
		self.savepath = self.parentpath+self.shortname+'/'
		mpi.mkdir(self.savepath, relative=False)

	def clear(self):
		for file in glob.glob(self.savepath+self.shortname+'_*'):
			os.remove(file)
