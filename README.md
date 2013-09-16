OSMeF
=====

The OpenStack Measurement Framework is used to measure the impact of virtualization in a
number of different scenarios, mostly centered around the traffic patterns generated by
Hadoop applications.

Right now OSMeF covers only networking end-to-end I/O and a couple of special cases to
measure the raw hypervisor virtual NIC performance. We plan to extend OSMeF to cover also
more complex communication patterns like one-to-many, many-to-many and many-to-one. Disk I/O
will be another focus where OSMeF can be used.

Quick start
-----------
OSMeF is divided in two directories, because of dependencies to Python2 in the paramiko
ssh library.

The `backend` directory contains OSMeF itself along woth the scenarios.

The `data_processing` directory contains scripts that load OSMeF output and produce
human-readable data.

Backend
-------
OSMeF is run by using one of the scripts in the `scenarios/` directory. Their name should be
self explanatory, but more documentation will follow this first release.

Some of the scenarios require a password-less ssh key to be provided, you need to modify
`config.ini` and the scenario script to provide to correct details.

Also IP addresses need to be appropriately configured in the scenario script.

Finally you need to fill-in the `template_login` file with the authentication details of
the OpenStack's tenant you want to use for running the experiments. These `*_login` files
are referenced in the `common.def` file.

Data processing
---------------
By default measurements will be saved in json format in the `output/results` directory.
A number of script in the `data_processing` directory helps with examining the data,
summarizing it and drawing graphs.

A note on Python versions
-------------------------
OSMeF itself runs with Python 2.7. The ssh library `paramiko`, that is not compatible with
Python 3.

The `data_processing` tools instead require Python 3.3.

The plan is to port everything on Python 3, once there is a suitable SSH library.

Acknowledgments
---------------
The OSMeF project is part of the [BigFoot project](http://bigfootproject.eu)

