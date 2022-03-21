Image Track
===========

This is the code for the LIMS system we use to manage imaging data from the range of instruments we have in the imaging facility.  It's a relatively lightweight system which simply records a set of metadata from different imaging projects and then creates a structured system of folders under which the data from different projects can then be stored.

There are no restrictions on read/write access to the data on the imaging systems so this system operates on trust at the point of project creation, however we can potentially incorporate the information in this system into our virtual filesystem on the cluster so we can provide wider controlled access to the data once the projects are created.
