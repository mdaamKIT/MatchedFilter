# MatchedFilter
An amateur pycbc interface for personal use or educational use, (hope-)fully compatible with windows.

Currently the software is in a kind of a beta phase. It should be fully functional (tested on a windows and a linux machine) and is mostly feature-complete. Refinements and code-cleanup are still to be done and a true version 1.0 is expected to be released in March 2024.

Feel free to start using the software from now on. You might sent me feedback to the email below.
You can also contact me, if you would like to contribute. 
Especially if you plan to use it on a Mac, it could be helpful to contact me, since I was not able to test the software on a Mac myself.

## Author and contact
* author: Michael Daam
* mail:   michael.daam@kit.edu


## License and Credit

The MatchedFilter software is published under the terms of the 'GNU General Public License Version 3' and you should find a copy of it here in the LICENSE file.

Credit goes to all the developers of the following software packages listed in the Section 'Dependencies'.
Especially relevant is the [PyCBC package][https://pycbc.org/] since the MatchedFilter is basically a graphical user interface to acces some of its features.


## Dependencies

The MatchedFilter is a python application, so you obviously need python installed on your machine and the python packages listed in the 'Python' subsection.

To use the MatchedFilter, you need docker. This makes the PyCBC-software accesible on windows.
(At the moment, docker is even used, if you use it on a Mac or on linux. This will be removed with the release of version 1.0.)


### Python

You need to have those python packages installed, to be able to run the MatchedFilter software.

sys
os
ast
pathlib
time
configparser

numpy
matplotlib

PyQt5
threading (re-check, if this is truly necessary anymore)

docker


### Docker

You need the docker software and at least a personal subscription. As of February 2024, a personal subscription is free of charge and allows for use in educational settings. But these terms are not under my control, not guaranteed by my and could potentially change in the future.

[https://www.docker.com/products/docker-desktop/][https://www.docker.com/products/docker-desktop/]

To use docker on your machine, you have to have permissions to do so. See [https://docs.docker.com/desktop/windows/permission-requirements/][https://docs.docker.com/desktop/windows/permission-requirements/]


## Short user manual

### Starting the application

1. [Download and potentially unzip the software.][https://github.com/mdaamKIT/MatchedFilter]
2. Start the docker application.
3. Go to the MatchedFilter-directory.
4. Open the matchedfilter.py with python. (E.g. 'python matchedfilter.py' from a terminal/shell.)

### Using the application

The purpose of the application is to analyze data gained from educational experiments to teach gravitational wave analysis. We use it together with a Michelson-Interferometer (one mirror glued to a piezo) as detector in an analogy to gravitational wave detection.

The software enables you 
1. to create .wav files resembling gravitational waves (in time domain) from compact binary coalescences (merging black holes and/or neutron stars) to feed into your (analogy-)detector. 
2. to create .hdf files resembling gravitational waves in frequency domain to use for the matched filtering.
3. to do the matched filtering.

I hope the use of the software is mostly self-explanatory. A more detailed user manual may be shipped out with version 1.0. If you already know the software by now, you are likely to have heard of it by me personally and you should already have a coarse idea of how it is used.
The software calculates the normalized 'match' quantity during matched filtering. This is 1.0 if the analyzed data are identical to the template and most of the times around 0.1 to 0.2 if the signals are randomly uncorrelated. The results of the analysis are by default stored to files in a folder of the same name as the analyzed data. A 3D-plot of the match versus the parameters (masses) of the templates can be created from the software.


## Advanced user manual

### notes

1. In the config.ini file, you can edit settings for which mergerplots to create. (Describe, how it works.)
