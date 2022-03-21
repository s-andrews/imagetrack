Installation Instructions
=========================

These instructions are for setting up the system on a base installation of RHEL (or equivalent) 8.


Check out the project codebase
------------------------------

First we need to grab a copy of the current codebase.

```
cd /srv/
sudo git clone https://github.com/s-andrews/imagetrack.git
```

We'll also change the permissions so the code is not owned by root. Here we're using the limsadmin account but you can use whichever user makes sense on your system.

```
sudo chown -R limsadmin imagetrack/
```

Mount the imaging store
=======================

The system is going to need to know where the data for the imaging facility is.  We therefore need to mount the imagestore share onto the server.

We do this by adding the share definition to the main ```/etc/fstab``` file, and then mounting from there.  Again, the information I show here is illustrative, but would need to be changed to the actual location of the share and where you wanted it mounted.

We need to create a folder in which to mount it:

```
sudo mkdir /mnt/imagedatastore
```

Then, the line for ```/etc/fstab``` is:

```
central-cluster:/ifs/Institute/ImageDataStore1/Image\040Facility\040User\040Data   /mnt/imagedatastore  nfs rsize=32768,wsize=32768,hard,fg,lock,rw,nfsvers=3,tcp 0 0
```


Configure the web server
====================================

We need to put the apache conf file in the distribution in a folder so that apache will recognise it:

```
sudo ln -s /srv/imagetrack/configuration/imagetrack_apache.conf /etc/httpd/conf.d/

sudo systemctl restart httpd
```






