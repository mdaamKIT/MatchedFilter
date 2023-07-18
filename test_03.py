#!/usr/bin/python3

import templatebank_handler as handler

# Set up connection

# output_host = '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/03_ctm/output_dir/'
# output_container = '/output/'

connection = handler.connect()


# Define paths and filenames

data_path = '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/03_ctm/data_dir/'
data_filename = '10-10.wav'

template_path = '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/03_ctm/templates/'
template_filename = '10-10.hdf'


# working with handler-objects

template = handler.Template(template_path, template_filename)
data = handler.Data(data_path, data_filename)

data.matched_filter_single(template, connection)