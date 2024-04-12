#!/usr/bin/env python3

from pycbc.waveform import get_td_waveform,td_approximants
from pycbc import types
from pycbc.filter import matched_filter_core, sigmasq #, matched_filter, match
import numpy as np
import matplotlib.pyplot as plt
import os

import wave
import resampy
import h5py

from collections import defaultdict
from datetime import datetime
from configparser import ConfigParser
from json import loads as jsonloads

### About
#   -----

# This file seeks to define some useful functions to use the pycbc-functions in my lab.


### Global definitions
#   ------------------

config = ConfigParser()
config.read('config.ini')
debugmode = config.getboolean('main', 'debugmode')

# approximants for template creation
APX_DEFAULT = config.get('approximants', 'apx_default')
if not config.getboolean('approximants', 'use_backup'):
	APX_ALL = td_approximants()
	APX_FORBIDDEN = jsonloads(config.get('approximants', 'apx_forbidden')) # Trying these apxs caused python to crash with a "Segmentation fault (core dumped)" - an exception it could not handle.
	APX_ALLOWED = list(set(APX_ALL).difference(APX_FORBIDDEN, [APX_DEFAULT]))
else:
	APX_ALLOWED = jsonloads(config.get('approximants', 'apx_backup'))


### Redefine classes inside the container
#   -------------------------------------

# It is just more handy to input an object as an argument of a function than every of its properties seperately.
# This is why I decided to transfer the Template and Data objects from the templatebank_handler on the host machine in here.
# I guess I don't need any methods for changing values as these objects probably won't live long enough
# since the container will have to be restarted quite a few times.

class TemplateBank:
	def __init__(self):
		self.list_of_templates = []
	
	def add_template(self, bankpath, filename):
		'Add a single file to the TemplateBank.'
		self.list_of_templates.append(Template(bankpath, filename))

class Template:
	def __init__(self, path, filename):
		self.path = path
		self.filename = filename
		self.shortname = filename[:-4]

		self.frequency_series, self.m1, self.m2 = load_FrequencySeries(self.path+self.filename)

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

class NaNError(Exception):
	pass

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
# Note: datetime.timedelta objects can just be added and subtracted to/from each other.

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
	newtrack = resampy.resample(track, samplerate, preferred_samplerate)  # resampling with pycbc did not work, since the recording samplerate is not right. (I guess would have to be a multiple of 2.)
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


def make_template( m1, m2, apx='SEOBNRv4', samplerate=4096, duration=1.0, flag_show=False ):
	'Create a template in frequency-domain or time-domain or both.'

	# some hard-coded settings
	spin = 0.9
	f_low = 30         # I could use something above 50Hz to exclude line frequency transmitted by the amplifier. (But in my setup, 50 Hz line freq is not an issue.)

	# create time-domain template and reshape to exactly fit duration but only at max half full. (At max half full, to avoid wraparound-problems in merger-time determination.)
	hp, _ = get_td_waveform(approximant=apx,
	                             mass1=m1,
	                             mass2=m2,
	                             spin1z=spin,
	                             delta_t=1.0/samplerate,
	                             f_lower=f_low)             # (we only use plus polarization)
	durdiff = hp.duration-0.5*duration
	if durdiff>0:
		hp=hp.crop(durdiff,0)
	durdiff = duration-hp.duration
	hp.prepend_zeros(int(durdiff*samplerate))

	if flag_show:
		plt.plot(hp.sample_times, hp)
		plt.ylabel('Strain')
		plt.xlabel('Time (s)')
		plt.title('Merger-Template '+str(int(m1))+','+str(int(m2)))
		plt.show()

	# transform to a FrequencySeries
	hp_freq = hp.to_frequencyseries()

	return hp_freq, hp


def make_template_any_apx( m1, m2, samplerate=4096, duration=1.0, flag_show=False, errorname='nameless_template' ):
	'Create a template. Try all allowed approximants (apx), if default apx fails.'
	try:
		hp_freq, hp = make_template(m1, m2, apx=APX_DEFAULT, samplerate=samplerate, duration=duration, flag_show=flag_show)
		if np.isnan(hp_freq[0]) or np.isnan(hp[0]):
			raise NaNError
		return hp_freq, hp
	except:
		print('Creating template with default approximant ('+APX_DEFAULT+') failed. Trying other ones.')
		for apx in APX_ALLOWED:
			try:
				hp_freq, hp = make_template(m1,m2,apx=apx, samplerate=samplerate, duration=duration, flag_show=flag_show)
				if np.isnan(hp_freq[0]) or np.isnan(hp[0]):
					raise NaNError
				print('Creating template with other approximant ('+apx+') worked.')
				return hp_freq, hp
			except NaNError:
				pass              # Custom Error only caused by Frequency-/or TimeSeries starting with a nan. Continue trying the other approximants.
			except RuntimeError:
				pass              # Probalby the approximant could not handle this particular set of parameters. Just continue trying the other approximants.
	errorstring = errorname+' ('+str(datetime.now())+'): None of the approximants was able to create a template with masses '+str(m1)+' and '+str(m2)+'.\n'
	print(errorstring)
	with open(savepath+'errors.txt', 'a') as errorfile:
		errorfile.write(errorstring)


def save_FrequencySeries(freq_series, path, m1, m2):
	'Modified copy of (parts of) pycbcs save() fct. in FrequencySeries to also save the masses.'
	key = 'data'
	with h5py.File(path, 'a') as f:
		ds = f.create_dataset(key, data=freq_series.numpy(), compression='gzip', compression_opts=9, shuffle=True)
		if freq_series.epoch is not None:
			ds.attrs['epoch'] = float(freq_series.epoch)
		ds.attrs['delta_f'] = float(freq_series.delta_f)
		ds.attrs['m1'] = m1
		ds.attrs['m2'] = m2



def load_FrequencySeries(path):
	'Modified copy of (parts of) pycbcs types.frequencyseries.load_frequencyseries() to also load the saved masses.'
	key = 'data'
	with h5py.File(path, 'r') as f:
		data = f[key][:]
		delta_f = f[key].attrs['delta_f']
		epoch = f[key].attrs['epoch'] if 'epoch' in f[key].attrs else None
		series = types.frequencyseries.FrequencySeries(data, delta_f=delta_f, epoch=epoch)
		m1 = 0.
		m2 = 0.
		try:
			m1 = f[key].attrs['m1']
			m2 = f[key].attrs['m2']
		except NameError:
			print('File ',path,' does not have masses m1, m2 as attributes; seems not to be created by the latest version of this software.')
	return series, m1, m2



def create_templates(parameters, savepath, basename, attribute, freq_domain, time_domain):
	'Creates templates for further use in matched filtering (freq_domain) or as signals (time_domain).'
	# parameters should be a numpy array of dim 2xN; flag_Mr, freq_domain and time_domain should be boolean.
	# keyword parameter should be either 'individual', 'total', or 'chirp'

	# transform parameters to m1,m2, if necessary
	N = len(parameters[0])
	np.savetxt(savepath+'00_progress_create.dat', [0, N+1], fmt=['%i'])
	masses = parameters
	parameter_name = 'mm'
	if attribute == 'individual':
		for index in np.arange(N):
			if masses[0][index]<masses[1][index]:
				m1,m2 = masses[0][index], masses[1][index]
				masses[0][index], masses[1][index] = m2,m1
	elif attribute == 'total':
		M = parameters[0]
		r = parameters[1]
		for index in np.arange(N):
			if r[index]>1:
				r[index] = 1./r[index]
		m1 = M/(r+1)
		m2 = r*m1
		masses = np.asarray((m1,m2))
		parameter_name = 'MR'
	elif attribute == 'chirp':
		Mc = parameters[0]
		r = parameters[1]
		for index in np.arange(N):
			if r[index]>1:
				r[index] = 1./r[index]
		m2 = Mc*np.power(np.power(r,3)+np.power(r,2), 0.2)
		m1 = m2/r
		masses = np.asarray((m1,m2))
		parameter_name = 'McR'
	else:
		raise ValueError('Keyword attribute should be individual, total or chrip but is '+str(attribute))

	# create names and make distinctions between names if necessary
	list_of_names = ['']*N
	for index in range(N):
		name_0 = str(round(parameters[0][index]))
		if attribute == 'individual':
			name_1 = str(round(parameters[1][index]))
		else:
			name_1 = str(int(np.round(1000*parameters[1][index]))).zfill(4) # str(round(parameters[1][index]*1000))
		list_of_names[index] = basename+parameter_name+'_'+name_0+'-'+name_1
	D = defaultdict(list)
	for i,name in enumerate(list_of_names):
		D[name].append(i)
	list_of_real_duplicates = []
	for name in D:
		duplicates = D[name][1:]
		for number,name_index in enumerate(duplicates):
			# add an appendix to create a unique name
			list_of_names[name_index] = list_of_names[name_index]+'_'+str(number+2)
			# identify, if not only name, but also parameters are duplicates
			for previous_index in D[name][:number+1]:
				if parameters[0][name_index]==parameters[0][previous_index] and parameters[1][name_index]==parameters[1][previous_index]:
					list_of_real_duplicates.append(name_index)

	# create templates
	for index,m1 in enumerate(masses[0]):
		if not os.path.isfile(savepath+'canceled.txt'):
			if not index in list_of_real_duplicates:
				np.savetxt(savepath+'00_progress_create.dat', [index+1, N+1], fmt=['%i'])
				m2 = masses[1][index]
				name = list_of_names[index]
				if 0.49<m1+m2<100.1 : # 0.49<m1<100.1 and 0.49<m2<100.1: <- this is what I wanted at first, but for some reason, runtime explodes with this.
					try:
						strain_freq, strain_time = make_template_any_apx(m1,m2, errorname=name)
						if time_domain: strain_time.save_to_wav(savepath+name+'.wav')
						if freq_domain: save_FrequencySeries(strain_freq, savepath+name+'.hdf', m1, m2)
					except ValueError:
						errorstring = name+' ('+str(datetime.now())+'): There was a ValueError; probably a .hdf-file of that name already existed.\n'
						print(errorstring)
						with open(savepath+'errors.txt', 'a') as errorfile:
							errorfile.write(errorstring)
					except:
						errorstring = name+' ('+str(datetime.now())+'): Unexpected Error with masses '+str(m1)+', '+str(m2)+'.\n'
						print(errorstring)
						with open(savepath+'errors.txt', 'a') as errorfile:
							errorfile.write(errorstring)
				else:
					if debugmode: 
						print('create_templates: omitting masses '+str(m1)+', '+str(m2)+' (out of range)')
		else:
			print('Template creation canceled by user.')
			os.remove(savepath+'canceled.txt')
			break
	# np.savetxt(savepath+'00_progress_create.dat', [N+1, N+1], fmt=['%i'])


def matched_filter_single(data, template):  # psd, f_low, these arguments were cut out now
	'Perform the matched filtering of data with a single template.'

	plot_snr = False

	tmp = template.frequency_series 							# readability
	offset = get_end_time(tmp.to_timeseries()).total_seconds() 	# offset of template end_time vs merger-time; in template t=0 is at merger.

	### initialize outputs
	num = len(data.segments)
	lenseg = len(data.segments[0])
	deltat = data.segments[0].delta_t
	matches = np.zeros(num)
	indices = np.zeros(num)
	times = np.zeros(num)
	phis = np.zeros(num)
	count_of_max = 0
	detail_match = 0.
	if plot_snr:
		# snr over whole data length ('full')
		lensnr = int(0.5*(num+1)*lenseg)
		snr_even = np.zeros(lensnr, dtype=np.complex128)
		snr_odd = np.zeros(lensnr, dtype=np.complex128)
		full_time = np.arange(lensnr)*deltat
		# snr around merger ('detail')
		detail_snr = np.zeros(lenseg, dtype=np.complex128)
		detail_time = np.zeros(lenseg)


	### matched filtering for all segments
	for count,segment in enumerate(data.segments):

		snr,_,snr_norm = matched_filter_core(tmp, segment) #, psd=psd, low_frequency_cutoff=f_low)
		# Following 4 lines: the pycbc matched_filter() and match() functions. Calling those two would calculate matched_filter_core() twice. 
		mf_out = snr*snr_norm                              # mf_out = matched_filter(...)
		v2_norm = sigmasq(segment)                         # match1,index1,phi1 = match(tmp, segment, return_phase=True)
		maxsnr, index1 = mf_out.abs_max_loc()
		match1 = maxsnr/np.sqrt(v2_norm)          # (maxsnr (mf_out) is already normed)
		if plot_snr:
			start = int(0.5*count*lenseg)
			end = start+lenseg
			if count % 2 == 0:
				snr_even[start:end] = mf_out
			else: snr_odd[start:end] = mf_out

		matches[count] = match1
		indices[count] = index1
		end_time = get_end_time(segment)
		times[count] = end_time.total_seconds() - segment.duration + index1/segment.sample_rate - offset
		phis[count] = np.angle(snr[int(round(index1))])

		if match1 > detail_match:
			count_of_max = count
			detail_match = match1
			if plot_snr:
				detail_snr = mf_out
				detail_time = np.arange(lenseg)*deltat+full_time[start]

		if False:
			plt.plot(mf_out.sample_times, abs(mf_out))
			plt.ylabel('signal-to-noise ratio')
			plt.xlabel('time (s)')
			plt.title('snr of '+data.shortname+' with '+template.shortname+' - '+str(count).zfill(2))
			plt.savefig(data.savepath+'SNR_'+data.shortname+'_'+template.shortname+'_'+str(count).zfill(2)+'.png')
			if data.flag_show: plt.show()
			else: plt.close()  
			
	# create and plot full snr
	if plot_snr:
		full_snr = np.maximum(snr_even, snr_odd)
		plt.plot(full_time, abs(full_snr))
		plt.ylabel('signal-to-noise ratio')
		plt.xlabel('time (s)')
		plt.title('snr of '+data.shortname+' with '+template.shortname+' - full')
		plt.savefig(data.savepath+'SNR_'+data.shortname+'_'+template.shortname+'_full.png')
		if data.flag_show: plt.show()
		plt.close()

	# plot detail snr
	if plot_snr:
		plt.plot(detail_time, abs(detail_snr))
		plt.ylabel('signal-to-noise ratio')
		plt.xlabel('time (s)')
		plt.title('snr of '+data.shortname+' with '+template.shortname+' - '+str(count_of_max).zfill(2))
		plt.savefig(data.savepath+'SNR_'+data.shortname+'_'+template.shortname+'_detail.png')
		if data.flag_show: plt.show()
		plt.close() 

	### get maximum values over all segments
	Maxmatch = [matches[count_of_max], times[count_of_max], phis[count_of_max], count_of_max, indices[count_of_max]]

	### plot template and data together
	# Plotting template and data together ('merger plot') is now done by calling the plot_merger function. (since v0.2)
	# Actually calling plot_merger is swapped out to the matched_filter_templatebank function, to save disc space by calling it only for the best matching templates.
	# In case all merger plots should be created, it is still executed here, to keep progress bar more meaningful.
	if config.getboolean('mergerplots', 'create_all'): plot_merger(data, template, Maxmatch)

	return matches, indices, times, phis, Maxmatch


def plot_merger(data, template, Maxmatch):
	'Plot data and template together at the time of best match.'

	### I should check, if data and template are respective objects.
	### Maybe Maxmatch should also be an object. (Maybe not, since I don't want it to persist in the memory.)

	### settings for plot should somehow come from the config-file

	tmp = template.frequency_series		# readability
	# settings for plot
	before = config.getfloat('mergerplots', 'time_before_merger')   # start plot *before* merger (in s)
	after = config.getfloat('mergerplots', 'time_before_merger')    # end        * after* merger (in s)
	# create arrays for plot 
	plot_data = data.segments[Maxmatch[3]]/np.sqrt(sigmasq(data.segments[Maxmatch[3]]))   # normed data segment.
	plot_time = plot_data.sample_times
	tmp_shift = np.exp(1j*Maxmatch[2])*tmp
	tmp_time = tmp_shift.to_timeseries()
	tmp_time = Maxmatch[0]/np.sqrt(sigmasq(tmp_time))*tmp_time
	index1 = int(Maxmatch[4])
	lenseg = len(data.segments[0])
	plot_tmp = np.concatenate( (np.asarray(tmp_time[(lenseg-index1):]), np.zeros(lenseg-index1)) )
	# plot
	offset = get_end_time(tmp.to_timeseries()).total_seconds() 	# offset of template end_time vs merger-time; in template t=0 is at merger.
	offset_ind = int(round(offset*plot_data.sample_rate))
	start = max( int(round(index1-before*plot_data.sample_rate))-offset_ind, 0)
	end = min( int(round(index1+after*plot_data.sample_rate))-offset_ind, lenseg)
	plt.plot(plot_time[start:end], plot_data[start:end], color='tab:blue', linestyle='-', marker=',')
	plt.plot(plot_time[start:end], plot_tmp[start:end], color='tab:red', linestyle=':', marker=',', linewidth=2., alpha=1.0) 
	plt.legend(['data', 'template'])
	plt.xlabel('time (s)')
	plt.ylabel('amplitude (a.u.)')
	plt.title(data.shortname+' and '+template.shortname+'; t = '+str(round(Maxmatch[1],3))+' s, match = '+str(round(Maxmatch[0],2)))
	plt.savefig(data.savepath+'plot_'+data.shortname+'_'+template.shortname+'.png')
	if data.flag_show: plt.show()
	plt.close() 


def matched_filter_templatebank(data, templatebank):
	'Perform the matched filtering of the data with every template inside a templatebank.'
	# prepare output
	num = len(templatebank.list_of_templates)
	np.savetxt(data.savepath+'00_progress_mf.dat', [0, num+2], fmt=['%i'])
	dtype = [('templatename', (np.str_,40)), ('maxmatch', np.float64), ('maxtime', np.float64), ('m1', np.float64), ('m2', np.float64), ('M', np.float64), ('r', np.float64), ('Mc', np.float64)]
	results = np.zeros((num,8))
	names = []
	maxmatches_all = []
	writedata = np.array(np.zeros(num), dtype=dtype)
	sortdata = np.array(np.zeros(num), dtype=dtype)
	# calculate output
	for index,template in enumerate(templatebank.list_of_templates):
		if not os.path.isfile(data.savepath+'canceled.txt'):
			np.savetxt(data.savepath+'00_progress_mf.dat', [index+1, num+2], fmt=['%i'])
			_,_,_,_,Maxmatch = matched_filter_single(data, template)
			maxmatches_all.append(Maxmatch)
			results[index] = index, Maxmatch[0], Maxmatch[1], template.m1, template.m2, template.m1+template.m2, template.m2/template.m1, np.power(template.m1*template.m2, 0.6)/np.power(template.m1+template.m2, 0.2)
			names.append(template.shortname)
			writedata[index] = template.shortname, Maxmatch[0], Maxmatch[1], template.m1, template.m2, template.m1+template.m2, template.m2/template.m1, np.power(template.m1*template.m2, 0.6)/np.power(template.m1+template.m2, 0.2)
		else:
			print('Matched filtering canceled by user.')
			break
	np.savetxt(data.savepath+'00_progress_mf.dat', [num+1, num+2], fmt=['%i'])
	# sorted output
	results_sorted = results[results[:,1].argsort()[::-1]]
	for index in range(num):
		sortdata[index] = names[int(results_sorted[index,0])], results_sorted[index,1], results_sorted[index,2], results_sorted[index,3], results_sorted[index,4], results_sorted[index,5], results_sorted[index,6], results_sorted[index,7]
		# create a merger plot for best matching templates
		if not config.getboolean('mergerplots', 'create_all'):
			if index < config.getint('mergerplots', 'min_number'):  # I refrain from updating the progress bar while plotting even if it takes a noticeable amount of time. 
				plot_merger(data, templatebank.list_of_templates[int(results_sorted[index,0])], maxmatches_all[int(results_sorted[index,0])])
			if index < config.getint('mergerplots', 'max_number') and results_sorted[index,1] > config.getfloat('mergerplots', 'match_threshold'):
				plot_merger(data, templatebank.list_of_templates[int(results_sorted[index,0])], maxmatches_all[int(results_sorted[index,0])])
	# save results
	header = 'Matched Filtering results of '+data.shortname+': \n'
	header += 'templatename, match, time of match, template-m1, template-m2, template-M, template-R, template-Mc'
	np.savetxt(data.savepath+'00_matched_filtering_results.dat', writedata, fmt=['%s', '%f', '%f', '%f', '%f', '%f', '%f', '%f'], header=header)
	# save results sorted by match
	header = 'Matched Filtering results of '+data.shortname+' (sorted by match): \n'
	header += 'templatename, match, time of match, template-m1, template-m2, template-M, template-R, template-Mc'
	np.savetxt(data.savepath+'00_matched_filtering_results_sorted.dat', sortdata, fmt=['%s', '%f', '%f', '%f', '%f', '%f', '%f', '%f'], header=header)
	np.savetxt(data.savepath+'00_progress_mf.dat', [num+2, num+2], fmt=['%i'])