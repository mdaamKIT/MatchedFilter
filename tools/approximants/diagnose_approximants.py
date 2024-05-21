from pycbc.waveform import td_approximants, get_td_waveform


### Define useful functions

class NaNError(Exception):
	pass


def make_template( m1, m2, apx, samplerate=4096, duration=1.0, flag_show=False ):  # slight modification of mpi.make_template(): apx now as an argument
	'Create a template in frequency-domain or time-domain or both.'

	# some hard-coded settings
	spin = 0.9
	f_low = 30         # I could use something above 50Hz to exclude line frequency transmitted by the amplifier.

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


def make_template_any_apx(m1,m2, apx_default, apx_allowed):

	try:
		hp_freq, hp = make_template(m1, m2, apx=apx_default)
		return hp_freq, hp
	except:
		print()
		print('Creating template with default approximant ('+apx_default+') failed. Trying other ones.')
		print()
		for apx in apx_allowed:
			try:
				print('Try to create template with approximant '+apx+'.')
				hp_freq, hp = make_template(m1,m2,apx=apx)
				if np.isnan(hp_freq[0]) or np.isnan(hp[0]):
					raise NaNError
				print('Creating template with approximant '+apx+' worked.')
				return hp_freq, hp
			except NaNError:
				pass              # Custom Error only caused by Frequency-/or TimeSeries starting with a nan. Continue trying the other approximants.
			except RuntimeError:
				pass              # Probalby the approximant could not handle this particular set of parameters. Just continue trying the other approximants.


def diagnose_list(m1,m2, list_of_apx):

	for apx in list_of_apx:
		print(apx, ': trying to make a template...')
		try:
			hp_freq, hp = make_template(m1, m2, apx=apx)
			print(apx, ': successful.')
			print()
		except NaNError:
			print(apx, ': failed, but not fatal.')
			print()             # Custom Error only caused by Frequency-/or TimeSeries starting with a nan. Continue trying the other approximants.
		except RuntimeError:
			print(apx, ': failed, but not fatal.')
			print()              # Probalby the approximant could not handle this particular set of parameters. Just continue trying the other approximants.


def diagnose(m1,m2,apx_forbidden):

	apx_all = td_approximants()
	print('Diagnosing approximants on this machine')
	print('---------------------------------------')
	print()
	print('all available approximants:')
	print(apx_all)
	print()
	print('specified forbidden approximants:')
	print(apx_forbidden)
	print()
	print('Trying all approximants but forbidden ones.')
	print('Mass parameters for the test: ',m1,', ',m2)
	print()
	apx_allowed = list(set(apx_all).difference(apx_forbidden))
	diagnose_list(m1,m2,apx_allowed)


### Start diagnose

apx_default = 'SEOBNRv4'
apx_all = td_approximants()
apx_forbidden = ['SEOBNRv4', 'EOBNRv2_ROM', 'EOBNRv2HM_ROM', 'IMRPhenomXP', 'PhenSpinTaylor', 'PhenSpinTaylorRD', 
	'SEOBNRv1_ROM_DoubleSpin', 'SEOBNRv1_ROM_EffectiveSpin', 'SEOBNRv2_ROM_DoubleSpin', 'SEOBNRv2_ROM_DoubleSpin_HI', 'SEOBNRv2_ROM_EffectiveSpin', 
	'SEOBNRv4_ROM_NRTidalv2', 'SEOBNRv1', 'SEOBNRv2', 'SEOBNRv2_opt', 'TaylorF2NL']
apx_allowed = list(set(apx_all).difference(apx_forbidden))


m1 = 5.
m2 = 5.
diagnose(m1, m2, apx_forbidden)