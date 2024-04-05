from pycbc.waveform import td_approximants, get_td_waveform


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




apx_default = 'SEOBNRv4'   # by now I just randomly picked any
apx_all = td_approximants()
apx_forbidden = ['SEOBNRv4', 'EOBNRv2_ROM', 'EOBNRv2HM_ROM', 'IMRPhenomXP', 'PhenSpinTaylor', 'PhenSpinTaylorRD', 
	'SEOBNRv1_ROM_DoubleSpin', 'SEOBNRv1_ROM_EffectiveSpin', 'SEOBNRv2_ROM_DoubleSpin', 'SEOBNRv2_ROM_DoubleSpin_HI', 'SEOBNRv2_ROM_EffectiveSpin', 
	'SEOBNRv4_ROM_NRTidalv2']
apx_allowed = list(set(apx_all).difference(apx_forbidden))


apx_Jan2024 = ['TaylorT1', 'TaylorT2', 'TaylorT3', 'SpinTaylorT1', 'SpinTaylorT4', 'SpinTaylorT5', 'PhenSpinTaylor', 'PhenSpinTaylorRD', 'EOBNRv2', 'EOBNRv2HM', 'TEOBResum_ROM', 'SEOBNRv1', 'SEOBNRv2', 'SEOBNRv2_opt', 'SEOBNRv3', 'SEOBNRv3_pert', 'SEOBNRv3_opt', 'SEOBNRv3_opt_rk4', 'SEOBNRv4', 'SEOBNRv4_opt', 'SEOBNRv4P', 'SEOBNRv4PHM', 'SEOBNRv2T', 'SEOBNRv4T', 'SEOBNRv4_ROM_NRTidalv2', 'SEOBNRv4_ROM_NRTidalv2_NSBH', 'HGimri', 'IMRPhenomA', 'IMRPhenomB', 'IMRPhenomC', 'IMRPhenomD', 'IMRPhenomD_NRTidalv2', 'IMRPhenomNSBH', 'IMRPhenomHM', 'IMRPhenomPv2', 'IMRPhenomPv2_NRTidal', 'IMRPhenomPv2_NRTidalv2', 'TaylorEt', 'TaylorT4', 'EccentricTD', 'SpinDominatedWf', 'NR_hdf5', 'NRSur7dq2', 'NRSur7dq4', 'SEOBNRv4HM', 'NRHybSur3dq8', 'IMRPhenomXAS', 'IMRPhenomXHM', 'IMRPhenomPv3', 'IMRPhenomPv3HM', 'IMRPhenomXP', 'IMRPhenomXPHM', 'TEOBResumS', 'IMRPhenomT', 'IMRPhenomTHM', 'IMRPhenomTP', 'IMRPhenomTPHM', 'SEOBNRv4HM_PA', 'pSEOBNRv4HM_PA', 'IMRPhenomXAS_NRTidalv2', 'IMRPhenomXP_NRTidalv2', 'IMRPhenomXO4a', 'ExternalPython', 'TaylorF2', 'SEOBNRv1_ROM_EffectiveSpin', 'SEOBNRv1_ROM_DoubleSpin', 'SEOBNRv2_ROM_EffectiveSpin', 'SEOBNRv2_ROM_DoubleSpin', 'EOBNRv2_ROM', 'EOBNRv2HM_ROM', 'SEOBNRv2_ROM_DoubleSpin_HI', 'SEOBNRv4_ROM', 'SEOBNRv4HM_ROM', 'IMRPhenomD_NRTidal', 'SpinTaylorF2', 'TaylorF2NL', 'PreTaylorF2', 'SpinTaylorF2_SWAPPER']
apx_testfail = ['SEOBNRv4', 'SEOBNRv4_opt', 'SEOBNRv4P', 'SEOBNRv4PHM']
# 'SEOBNRv1', 'SEOBNRv2', 'SEOBNRv2_opt', 'SEOBNRv3', 'SEOBNRv3_pert', 'SEOBNRv3_opt', 'SEOBNRv3_opt_rk4', 

m1 = 5.
m2 = 5.
make_template_any_apx(m1, m2, apx_default, apx_testfail)