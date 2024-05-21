
# Known bugs and minor issues in the MatchedFilter software

To my current knowledge, the MatchedFilter software should run on Windows and linux without fatal bugs. (mdaamKIT, May 2024)


## Operating on any machine

### Stopping the threads (create templates / matched filtering)

This threads can be time consuming, therefore there is a cancel method implemented. Depending on the operating system, these threads might be performed inside Docker containers which makes it a little more complicated, to interrupt them.

- *[ugly:]* Aborting the processes inside the container by writing a `canceled.txt.` file into the containers directory doesn't seem pretty to me, but it works.
- *[cosmetic:]* Using the cancel button to interrupt these processes causes the GUI to freeze for a moment.




## Only on Windows

### Progress Bar

- *[cosmetic:]* After finishing the processes with a progress bar (Matched Filtering or Template Creation), an empty progress bar pops up multiple times.


## Only on linux

### Running docker as root

- *[ugly but unimportant:]* On my linux machine, the docker containers are run by root user. This means that the files created are owned by root and can't be changed easily by a non-root user. Especially the `00_progress_mf.dat` and `00_progress_create.dat` files to report the status of the processes of Matched Filtering or Template Creation to the progress bar do not get removed automatically. This is not important, since the docker containers are not necessary on linux anyway. 
I tried to solve this issue but I did not find a flexible solution that works on any machine. I only found solutions that would require to write (hard code) the alternate (non-root) user id somewhere, either in the `communicate_to_mpi_windows.MPIConnection.run()` command by using the user="uid:gid" parameter or in the docker-file. In the docker-file it should even be possible to be a little more flexible to write the id of the user compiling the docker-file into the docker-image. (Maybe that is nonsense.) That solution would anyway require the user to compile the docker-file by themselves. Facing those alternatives, I chose to keep going with the minor problem of having all those files owned by root. (Maybe that is not ideal from a security standpoint, but I did not expect my software to be used in very sensitive contexts. Feel free to change this behaviour in your copy of the software.)
All of this does not seem to be a problem on windows machines. Maybe the docker client is handling those issues well on windows?
(I could try podman instead of docker, if necessary.)


## Only on MacOS

The entire software has never been tested on MacOS. I hope, the software will work equally well as on linux, but there is no guarantee until tested.

If you ever run this software on a Mac, I would be happy to hear from you, no matter what the result was.
