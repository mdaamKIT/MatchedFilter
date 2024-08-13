# MatchedFilter

A grahical user interface (GUI) for some functions of the software [PyCBC](https://pycbc.org/) that is compatible with windows and intended for personal or educational use. PyCBC is a python package developed to analyse measurement data from graviational wave detectors as LIGO and Virgo. The purpose of the MatchedFilter GUI is to enable students without programming skills to analyze their own measurement data in an analogy lab. 

If you are using the software, feel free to sent me feedback to the email below.
You can also contact me, if you would like to contribute. 




## Author and contact

* author: Michael Daam
* mail:   michael.daam@kit.edu




## License and Credit

The MatchedFilter software is published under the terms of the 'GNU General Public License Version 3' and you should find a copy of it here in the LICENSE file.

Credit goes to all the developers of the following software packages listed in the section Installation and Dependencies.
Especially relevant is the [PyCBC package](https://pycbc.org/) since the MatchedFilter is basically a graphical user interface to acces some of its features.

If you are using the MatchedFilter software in a scientific publication, then you are indirectly using the PyCBC package and you should respect [their citation guidelines.](http://pycbc.org/pycbc/latest/html/credit.html)
We also ask you to credit our work. At the moment, the best form would be to reference the [github repository.](https://github.com/mdaamKIT/MatchedFilter) We are currently working on a publication that can be referenced in the future and will added here after publication.




## Installation and Dependencies

The MatchedFilter application is built around the python package PyCBC. This package is available on Linux and MacOS but not on Windows. To handle this issue, the software is equipped with the ability to create Docker containers where it can run the PyCBC commands, even on a Windows machine. This would be unnecessary overhead on Linux and therefore, installation and dependencies depend on the machine, you are using the software on.

Using it on a Mac is a special case, and it can be tried to use the MatchedFilter on a Mac either way - directly as on Linux or with the Docker workaround as on Windows. More details below in the MacOS subsection.


### Linux

You only need to have Python 3 installed and the following packages, to be able to run the MatchedFilter software on Linux:

- pycbc
- sys, os, ast, wave, configparser, collections, datetime, json (typically preinstalled in any Python version)
- numpy, matplotlib, h5py, samplerate, PyQt5

You do not need to install anything else.


### Windows

On a Windows PC, we need docker to handle the calls  of PyCBC function, so we need to have Docker installed in addition to python.

#### Python

You need to have Python 3 installed and you need the following packages, to be able to run the MatchedFilter software on Windows:

- sys, os, pathlib, ast, configparser (typically preinstalled in any Python version)
- numpy, matplotlib, PyQt5
- docker

#### Docker

If you are using Windows, you need the Docker desktop application and at least a personal subscription. As of February 2024, a personal subscription is free of charge and allows for use in personal or educational settings. But these terms are not under my control, not guaranteed by my and could potentially change in the future.

[https://www.docker.com/products/docker-desktop/]([https://www.docker.com/products/docker-desktop/)

To use docker on your machine, you have to have permissions to do so. See [https://docs.docker.com/desktop/windows/permission-requirements/](https://docs.docker.com/desktop/windows/permission-requirements/)


### MacOS

The MatchedFilter should in theory run on a Mac just as it does on Linux, but once I tried and it did not. There was a 'Bus error: 10' indicating problems with memory handling that might be connected how I use PyQt5 for the GUI, especially for threading.
This problem might be solvable, but I did not manage.
It might also be the case that this problem does not occur on every Mac but only on some architecture.

What should work in any case, is using the same Docker-based workaround as on Windows. When I tested this, it was quite slow compared to the performance I perviously experienced on my Linux and Windwos PCs and this seems to be common for Docker on a Mac. Anyway, it works.

So what is my recommendation for Mac users? If in doubt, install the MatchedFilter as described in the Windows subsection. 
For the best performance, you might want to try to install the MatchedFilter software as described in the Linux subsection. But you would have to expect it to possibly crash. In that case or to avoid the hustle, you could go back to installing as in the Windows subsection.

There is one important detail to note, if you want to change from using as on Linux to using as on Windows or the other way around: the MatchedFilter does not automatically know and you need to open the config.ini file and change the variable 'os' in '[main]' from 'linux' to 'windows' (or the other way around).

A last note: I do not own a Mac myself, and testing was very limited. Everything written here is based on installing the MatchedFilter once on one specific Mac.
If you encounter unforseen problems or solutions, feel free to contact me.




## Short user manual

### Downlaod and first start of the application

1. [Download and potentially unzip the software.](https://github.com/mdaamKIT/MatchedFilter/releases)
2. (On Windows / MacOS with docker: Download and start the Docker Desktop application, login with your Docker account and pull the image mdaamkit/mpi. You can use the search bar at the top of the Docker Desktop Window to find and pull images.)
3. Go to the MatchedFilter directory.
4. Open the matchedfilter.py with python. (E.g. enter `python matchedfilter.py` in a command line.)
5. A 'Setup on first startup' window should open where you need to specify if you want to use Docker. Select 'Yes' on Windows / MacOS with Docker and 'No' on Linux or on MacOS without Docker. The other settings available here are not essential. After clicking the 'Done' button, the window should close itself and open the MatchedFilter application. This setup window only opens the first time, you start the MatchedFilter application. If you ever need to change the selected settings, open the config.ini file and manually change the settings or only change the 'firststartup' variable in '[main]' to 'True' if you want the setup window to show up again the next time, you open the MatchedFilter application.

### Subsequent starts of the application

1. (On Windows / MacOS with docker: Start the Docker Desktop application.)
2. Go to the MatchedFilter-directory.
3. Open the matchedfilter.py with python. (E.g. enter `python matchedfilter.py` in a command line.)


### Use the application

The purpose of the application is to analyze data gained from educational experiments to teach gravitational wave analysis. We use it together with a Michelson-Interferometer as detector (with one mirror glued to a piezo) in an analogy to gravitational wave detection. We are currently working on a publication to further describe the software will be referenced here after publication.

The software enables you: 
1. to create .wav files resembling gravitational waves (in time domain) from compact binary coalescences (merging black holes and/or neutron stars) to feed into your (analogy-)detector. (By connecting audio out of the computer to the piezo with a mirror.)
2. to create .hdf files resembling gravitational waves in frequency domain to use for the matched filtering.
3. to do the matched filtering.

We hope the use of the software is mostly self-explanatory.
The software calculates the 'match' quantity during matched filtering. The match is the normalized correlation of the analyzed data with all the previously chosen templates. The match is 1.0 if the analyzed data are identical to the template and most of the times around 0.1 to 0.2 if the data is randomly uncorrelated. A match of 0.4 or higher typically indicates having measured a template similar to the one the filter was matched to. The results of the analysis are by default stored in the same location where the analyzed data was found in a folder of the same name as the analyzed data. It is stored as a table in a .dat file. Additionally, the best matching templates are plotted together with the data for comparison. A 3D-plot of the match versus the parameters (masses) of the templates can be created from the software.


## Advanced user manual

### Notes

1. In the config.ini file, you can edit settings for which mergerplots to create. (See in 'Merger plots' below.)
2. MatchedFilter creates templates only with masses from 0.5 to 100 solar masses. Requesting other masses should not break the program but templates will simply not be created.
3. If you experience crashes of the MatchedFilter software while creating templates, read the file `00_note_on_approximants` in `MatchedFilter/tools/approximants`.
4. Feel free to contact me if necessary.

### Merger plots

For the best matching templates, the software automatically creates plots, where both the template and the data are shown. In the config.ini file in the section 'mergerplots', you can adjust, how many of them should be drawn. Drawing those plots is time consuming and drawing all of them (setting `create_all = True`) would considerably slow down the matched filtering process. Most of the times, you are only interessted in the merger plot for the best matching template.
In every matched filter search with our software, plots are drawn for the templates with the highest match, descending. If your template bank contained more template than `min_number`, then at least `min_number` of templates are drawn. (Default: `min_number = 5`) Additionally, a plot will be drawn for any template whose match surpasses the `match_threshold` (default: `match_threshold = 0.55`), up to a maximum of `max_number` of plots. (Default: `max_number = 15`)

The plots are only drawn around merger time, (the time in the data, at which the greatest match with the template occured,) and the time interval starts `time_before_merger` seconds before (default: `time_before_merger = 0.1`), and ends `time_after_merger` seconds after the merger time. (Default: `time_after_merger = 0.05`) Typically, only a short intervall around the merger time is of interest, and zooming out too far will hide all the details.


## Notes for developers

### Conventions

Names of directories are stored as strings and end with a '/'. This way, filenames can be concatenated through the simple concatenation of their strings (fullname = path+filename) instead of calling functions. (E.g. fullname = os.path.join(path, filename) )

### Known bugs

There is a `known_bugs.md` file.
