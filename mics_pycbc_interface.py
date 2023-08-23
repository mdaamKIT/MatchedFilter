#!/usr/bin/python3

import matplotlib.pyplot as plt
from pycbc.waveform import get_td_waveform
from pycbc import types
from pycbc.filter import matched_filter, match
import resampy     # https://resampy.readthedocs.io/en/stable/example.html
import os
import wave
import numpy as np
from collections import defaultdict

### About
#   -----

# This file seeks to define some useful functions to use the pycbc-functions in my lab.

### Redefine classes
#   ----------------

# It is just more handy to input an object as an argument of a function than every of its properties seperately.
# This is why I decided to transfer the Template and Data objects from the templatebank_handler on the host machine in here.
# I guess I don't need any methods for changing values as these objects probably won't live long enough
# since the container will have to be restarted quite a few times.

debugmode = True

class TemplateBank:
	def __init__(self):
		self.list_of_templates = []
	
	def add_template(self, bankpath, filename):
		'Add a single file to the TemplateBank.'
		self.list_of_templates.append(Template(bankpath, filename))
		if debugmode: print('Added ', self.list_of_templates[-1].shortname, ' to the TemplateBank.')
	
	# def add_directory(self, path):
	# 	'Add all .hdf-files in path to the TemplateBank.'
	# 	listofnames = [f for f in os.listdir(path) if f.endswith('.hdf')]
	# 	listofnames.sort()
	# 	for filename in listofnames:
	# 		self.add_template(path, filename)

class Template:
	def __init__(self, path, filename):
		self.path = path
		self.filename = filename
		self.shortname = filename[:-4]

		self.frequency_series = types.frequencyseries.load_frequencyseries(self.path+self.filename)

class Data:
	def __init__(self, datapath, filename, savepath, preferred_samplerate, segment_duration, flag_show):
		self.datapath = datapath
		self.filename = filename
		self.shortname = filename[:-4]
		self.savepath = savepath

		self.preferred_samplerate = preferred_samplerate
		self.segment_duration = segment_duration
		self.flag_show = flag_show

		self.segments = segment_data(datapath+filename, preferred_samplerate, segment_duration)



### Data handling functions
#   -----------------------

def mkdir( dirname, relative=True ):
	'Creates the directory dirname.'

	if relative:
		cwd = os.getcwd()+'/'
		dirname = cwd+dirname

	if not os.path.isdir(dirname):
		os.makedirs(dirname)

	return

def load_wav( filename, channel='unclear', debugmode=False ):
	'Load a single numpy-array from a wav-file. Works with mono and stereo.'
	# channel can be 'mono', 'left', 'right', 'average', 'greater', 'unclear'.
	# 'unclear' is changed to 'greater' if the file is stereo.
	# following: https://stackoverflow.com/questions/54174160/how-to-get-numpy-arrays-output-of-wav-file-format

	with wave.open(filename) as snd:

		buffer = snd.readframes(snd.getnframes())
		samplerate = snd.getframerate()
		
		# relabel the channel, if 'unclear'
		if channel == 'unclear':
			if snd.getnchannels() == 2:
				channel = 'greater'
			if snd.getnchannels() == 1:
				channel = 'mono'

		# calculate track, depending on channel-info
		try:
			if channel == 'mono':
				track = np.frombuffer(buffer, dtype=f'int{snd.getsampwidth()*8}')
			else:
				interleaved = np.frombuffer(buffer, dtype=f'int{snd.getsampwidth()*8}')
				# Reshape it into a 2D array separating the channels in columns.
				stereo = np.reshape(interleaved, (-1,snd.getnchannels()))
				left = stereo[:,0]
				right = stereo[:,1]

				if channel == 'left':
					track = left
				elif channel == 'right':
					track = right
				elif channel == 'average':
					track = 0.5*(left+right)
				elif channel == 'greater':
					if np.sum(np.square(right)) > np.sum(np.square(left)):
						track = right
					else:
						track = left
				else:
					raise ValueError('channel can only be: mono, left, right, average, greater, unclear. But I got: ',channel)
		except Exception as err:
			print(repr(err))
			return

		if debugmode:
			print()
			print('Loaded '+filename+' with channel-info '+channel)
			print('The loaded sample length is: ', len(track)/samplerate, 'sec.')
			print('Its samplerate is: ',samplerate , 'Hz')

	return samplerate,track


### Functions to handle lal.gpstime to datetime conversions
#   -------------------------------------------------------

# I didnt find a good way to manipulate LIGOTimeGPS objects, so I defined functions to make time definitions in pycbc.types.TimeSeries objects easier.
# Note that I didnt quite use the time properties in the TimeSeries in the originally intended way since I do not care for absolute times, calender days and so on.
# This is why I use GPS_EPOCH as the starting point of every set of loaded data.
# datetime.timedelta objects can just be added and subtracted.

import lal.gpstime as gps

def set_end_time(timeseries, timedelta):
	'Set the property end_time of a TimeSeries to GPS_EPOCH + timedelta.'

	# I could build in some insinstance-checks. (timeseries, timedelta)

	tzero = gps.GPS_EPOCH
	timeseries.end_time = gps.utc_to_gps(tzero+timedelta)

	return

def get_end_time(timeseries):
	'Get the property end_time of a TimeSeries as a datetime.timedelta object.'

	# I could build in some insinstance-checks. (timeseries, timedelta)

	tzero = gps.GPS_EPOCH
	end_time = gps.gps_to_utc(timeseries.end_time)-tzero

	return end_time




### Functions to load data and do the matched filtering
#   ---------------------------------------------------

def segment_data(filename, preferred_samplerate=4096, segment_duration=1):
	'Load a wav-file and return it as a list of TimeSeries of proper duration and samplerate for further analysis.'

	# load and resample with preferred_samplerate
	samplerate,track = load_wav(filename, channel='unclear')
	newtrack = resampy.resample(track, samplerate, preferred_samplerate)
	newtrack = newtrack.astype(np.float64)
	
	# fill with zeros till length is a multiple of segment_length / 2
	segment_length = segment_duration*preferred_samplerate  # this should be a multiple of two!
	k = max(int(np.ceil(len(newtrack)/(0.5*segment_length))), 2)
	newtrack.resize(int(k*0.5*segment_length), refcheck=False)

	# cut in overlapping pieces of length segment_length
	data_segments = []
	for index in range(k-1):
		start = int(index*0.5*segment_length)
		end = start+segment_length
		data_segments += [types.timeseries.TimeSeries(newtrack[start:end],delta_t=1./preferred_samplerate,epoch=index*0.5*segment_duration)]

	return data_segments


def make_template( m1, m2, samplerate=4096, duration=1.0, flag_show=False ):
	'Create a template in frequency-domain or time-domain or both.'

	# some hard-coded settings
	apx = 'SEOBNRv4'   # by now I just randomly picked any
	spin = 0.9
	f_low = 30

	# create and reshape time-domain template
	hp, _ = get_td_waveform(approximant=apx,
	                             mass1=m1,
	                             mass2=m2,
	                             spin1z=spin,
	                             delta_t=1.0/samplerate,
	                             f_lower=f_low)
	durdiff = hp.duration-duration
	if durdiff>0:
		hp=hp.crop(durdiff,0)
	else:
		hp.prepend_zeros(int(-durdiff*samplerate))

	if flag_show:
		plt.plot(hp.sample_times, hp)
		plt.ylabel('Strain')
		plt.xlabel('Time (s)')
		plt.title('Merger-Template '+str(int(m1))+','+str(int(m2)))
		plt.show()

	# transform to a FrequencySeries
	hp_freq = hp.to_frequencyseries()

	return hp_freq, hp


def create_templates(parameters, savepath, basename, flag_Mr, freq_domain, time_domain):
	'Creates templates for further use in matched filtering (freq_domain) or as signals (time_domain).'
	# parameters should be a numpy array of dim 2xN; flag_Mr, freq_domain and time_domain should be boolean.
	N = len(parameters[0])
	masses = parameters
	parameter_name = 'mm'
	if flag_Mr:
		M = parameters[0]
		r = parameters[1]
		m2 = M/(r+1)
		m1 = r*m2
		masses = np.asarray((m1,m2))
		parameter_name = 'Mr'

	# create names and make distinctions between names if necessary
	list_of_names = ['']*N
	for index in range(N):
		name_0 = str(round(parameters[0][index]))
		name_1 = str(round(parameters[1][index]))
		if flag_Mr:
			name_1 = str(round(parameters[1][index]*1000))
		list_of_names[index] = basename+parameter_name+'_'+name_0+'-'+name_1
	D = defaultdict(list)
	for i,name in enumerate(list_of_names):
		D[name].append(i)
	list_appendices = []
	for name in D:
		duplicates = D[name][1:]
		for number,name_index in enumerate(duplicates):
			list_of_names[name_index] = list_of_names[name_index]+'_'+str(number+2)

	for index,m1 in enumerate(masses[0]):
		m2 = masses[1][index]
		name = list_of_names[index]
		# The pycbc-function in use raises a RuntimeError, if die Ringdown frequency is too high which occurs often with low masses.
		try:
			strain_freq, strain_time = make_template(m1,m2)
		except RuntimeError:
			errorstring = name+': There was a RuntimeError; probably your masses '+str(m1)+', '+str(m2)+' were too low.\n'
			print(errorstring)
			with open(savepath+'errors.txt', 'a') as errorfile:
				errorfile.write(errorstring)
		except:
			errorstring = name+': unexpected Error with masses '+str(m1)+', '+str(m2)+'\n'
			print(errorstring)
			with open(savepath+'errors.txt', 'a') as errorfile:
				errorfile.write(errorstring)
		if freq_domain: 
			try:
				strain_freq.save(savepath+name+'.hdf')
			except ValueError:
				pass
		if time_domain: strain_time.save_to_wav(savepath+name+'.wav')


		

def matched_filter_single(data, template):  # psd, f_low, these arguments were cut out now
	'Perform the matched filtering of data with a single template.'

	tmp = template.frequency_series  # readability

	debugmode = False

	# calc offset of template end_time vs merger-time
	offset = get_end_time(tmp.to_timeseries()).total_seconds()

	num = len(data.segments)
	lenseg = len(data.segments[0])
	deltat = data.segments[0].delta_t
	matches = np.zeros(num)
	indices = np.zeros(num)
	times = np.zeros(num)

	lensnr = int(0.5*(num+1)*lenseg)
	snr_even = np.zeros(lensnr, dtype=np.complex128)
	snr_odd = np.zeros(lensnr, dtype=np.complex128)
	full_time = np.arange(lensnr)*deltat
	
	detail_snr = np.zeros(lenseg, dtype=np.complex128)
	detail_time = np.zeros(lenseg)
	detail_match = 0.
	count_of_max = 0

	for count,segment in enumerate(data.segments):
		snr = matched_filter(tmp, segment)#, psd=psd, low_frequency_cutoff=f_low)  # Signal-to-Noise Ratio. I am not yet sure, how to interpret that!
		start = int(0.5*count*lenseg)
		end = start+lenseg
		if count % 2 == 0:
			snr_even[start:end] = snr
		else: snr_odd[start:end] = snr

		### ------- isn't it a waste of computation, to calc both seperately: matched_filter (above) and match (below) ----- ###

		match1,index1,phi1 = match(tmp, segment, return_phase=True)                # match1 seems to be the value that is to be looked for.
		matches[count] = match1
		indices[count] = index1
		end_time = get_end_time(segment)
		times[count] = end_time.total_seconds() - segment.duration + index1/segment.sample_rate - offset

		if match1 > detail_match:
			detail_snr = snr
			detail_match = match1
			detail_time = np.arange(lenseg)*deltat+full_time[start]
			count_of_max = count

		if False:
			plt.plot(snr.sample_times, abs(snr))
			plt.ylabel('signal-to-noise ratio')
			plt.xlabel('time (s)')
			plt.title('snr of '+data.shortname+' with '+template.shortname+' - '+str(count).zfill(2))
			plt.savefig(data.savepath+'SNR_'+data.shortname+'_'+template.shortname+'_'+str(count).zfill(2)+'.png')
			if data.flag_show: plt.show()
			else: plt.close()  
			
	# create and plot full snr
	full_snr = np.maximum(snr_even, snr_odd)
	plt.plot(full_time, abs(full_snr))
	plt.ylabel('signal-to-noise ratio')
	plt.xlabel('time (s)')
	plt.title('snr of '+data.shortname+' with '+template.shortname+' - full')
	plt.savefig(data.savepath+'SNR_'+data.shortname+'_'+template.shortname+'_full.png')
	if data.flag_show: plt.show()
	else: plt.close()

	# plot detail snr
	plt.plot(detail_time, abs(detail_snr))
	plt.ylabel('signal-to-noise ratio')
	plt.xlabel('time (s)')
	plt.title('snr of '+data.shortname+' with '+template.shortname+' - '+str(count_of_max).zfill(2))
	plt.savefig(data.savepath+'SNR_'+data.shortname+'_'+template.shortname+'_detail.png')
	if data.flag_show: plt.show()
	else: plt.close() 

	# get maximum values
	Maxmatch = [matches[count_of_max],times[count_of_max]]

	return matches, indices, times, Maxmatch


def matched_filter_templatebank(data, templatebank):
	'Perform the matched filtering of the data with every template inside a templatebank.'
	# prepare output
	dtype = [('templatename', (np.str_,40)), ('maxmatch', np.float64), ('maxtime', np.float64)]
	writedata = np.array(np.arange(len(templatebank.list_of_templates)), dtype=dtype)
	# calculate
	for index,template in enumerate(templatebank.list_of_templates):
		_,_,_,Maxmatch = matched_filter_single(data, template)
		writedata[index] = template.shortname, Maxmatch[0], Maxmatch[1]
	# save statistics
	header = 'Matched Filteting results of '+data.shortname+': \n'
	header += 'templatename, match, time of match'
	np.savetxt(data.savepath+'00_matched_filtering_results.dat', writedata, fmt=['%s', '%f', '%f'], header=header)