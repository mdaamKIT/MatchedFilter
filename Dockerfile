
FROM python:3.9 
# I can't use newer version of python because numba does not support it, which is necessary for resampling with resampy.

ADD mics_pycbc_interface.py /
RUN mkdir /output
RUN mkdir /input

RUN pip install pycbc numpy matplotlib
RUN pip install wave resampy h5py
RUN pip install datetime configparser
