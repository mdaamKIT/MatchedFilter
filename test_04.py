#!/usr/bin/python3

import templatebank_handler as handler

# Set up connection


connection = handler.connect()

mpi_path_host = '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/'
mpi_path_container = '/input/mpi/'
connection.update_mpi(mpi_path_host, mpi_path_container)


# Define paths and filenames

data_path = '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/03_ctm/data_dir/'
data_filename = '10-10.wav'

templatebank_path = '/home/mic/promotion/f-prakt_material/LIGO/pycbc/MatchedFilter/tests/03_ctm/templates/'


# working with handler-objects

templatebank = handler.TemplateBank()
templatebank.add_directory(templatebank_path)

data = handler.Data(data_path, data_filename)

data.matched_filter_templatebank(templatebank, connection)