
FROM python:3.9 

RUN apt update && apt install -y cmake

COPY mics_pycbc_interface.py /
RUN mkdir /output /input

RUN pip install --no-cache-dir pycbc numpy matplotlib
RUN pip install --no-cache-dir wave samplerate h5py
RUN pip install --no-cache-dir datetime configparser
