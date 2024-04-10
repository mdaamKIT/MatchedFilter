import os
import mics_pycbc_interface as mpi

### About the templatebank_handler_linux
#   ------------------------------------

# This file should seem to be a bit needless at first glance. It would be, if the MatchedFilter software would be designed to run on linux/MacOs only.
# But to be able to run on Windows, its older brother, templatebank_handler_win.py is necessary. 
# That is because the pycbc package is not available on Windows, so a docker container is used as a workaround.
# Templatebank_handler_win manages the communication between the main application on the host (matchedfilter.py) 
# and the auxiliary interface for pycbc (mics_pycbc_interface, mpi) in the container. 

# This is not strictly necessary on a linux (or MacOS) machine, where the main application can directly call functions from pycbc or mpi.
# To keep differences between the windows and the linux version minimal, templatebank_handler_linux exists. 
# It is designed make it possible for the main application to call the mpi functions on linux exactly the same way it would on windows.
# I might not have found the most elegant solution to make this work, but a solution anyway.


class TemplateBank:
	def __init__(self):
		self.list_of_templates = []
	
	def add_template(self, bankpath, filename, flag_print=True):
		'Add a single file to the TemplateBank.'
		self.list_of_templates.append(Template(bankpath, filename))
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
		list_old_templates = [f for f in os.listdir(bankpath) if f.endswith('.hdf')]
		mpi.create_templates(array_masses, bankpath, basename, attribute, freq_domain, time_domain)
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
		mpi_templatebank = mpi.TemplateBank()
		for template in templatebank.list_of_templates:
			mpi_templatebank.add_template(template.bankpath, template.filename) # Not pretty, since every template now is two objects: one here in the handler and one in mpi. But it's easy and it works.
		mpi_data = mpi.Data(self.datapath, self.filename, self.savepath, self.preferred_samplerate, self.segment_duration, False)
		mpi.matched_filter_templatebank(mpi_data, mpi_templatebank)

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


def mkdir( dirname, relative=True ):
	'Creates the directory dirname.'
	if relative:
		cwd = os.getcwd()+'/'
		dirname = cwd+dirname
	if not os.path.isdir(dirname):
		os.makedirs(dirname)
	return