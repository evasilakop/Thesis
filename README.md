Tested in an anaconda environment on Windows 11 with the packages listed in the requirements.txt file.

Run each node with the following command format: python main.py -i (insert number 0-3 for node index, required)
                                                                -v (path to video file, samples provided)
                                                                -n (number of nodes in the group)

Needed to run:
python 3.12
opencv
miniconda3
SUMO dlr

add Python and Miniconda to PATH

allow TCP connections through the firewall for ports 5001-5004

in the anaconda environment, install with pip:
ultralytics

In the run_X_nodes.bat files, change the python path to point to your anaconda python