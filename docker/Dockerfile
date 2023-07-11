
# I can't use newer version of python because numba does not support it, which is necessary for resampling with resampy.
FROM python:3.9

ADD mics_pycbc_interface.py /
RUN mkdir /output

RUN pip install matplotlib numpy pycbc
RUN pip install wave resampy              # do we need this?
