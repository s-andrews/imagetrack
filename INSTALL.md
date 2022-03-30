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
central-cluster:/ifs/Institute/ImageDataStore1/LIMS_user_data   /mnt/imagedatastore  nfs rsize=32768,wsize=32768,hard,fg,nolock,rw,nfsvers=3,tcp,user,_netdev 0 0
```


Configure the web server
========================

We need to put the apache conf file in the distribution in a folder so that apache will recognise it:

```
sudo ln -s /srv/imagetrack/Configuration/imagetrack_apache.conf /etc/httpd/conf.d/

sudo systemctl restart httpd
```

We also need to remove the default ```/cgi-bin/``` configuration as it overrides the one in our package.  To do this we need to comment out the following line in ```/etc/httpd/conf/httpd.conf```

```
ScriptAlias /cgi-bin/ "/var/www/cgi-bin/"
```

Install python dependencies
===========================

We need some additional python packages and these are detailed in ```requirements.txt```.  The python setup on CentOS8 is a bit weird in that there are 

To install the OS packages we can run:

```
sudo dnf -y install python3-pymongo python3-bcrypt
```

Set up the database
===================

The back end for this system is a MongoDB database.  You will need to have a mongoDB server running, either locally or on a separate machine.

If you're running on a system with authentication enabled, and not just on a locally accessible database, then you will need to create a suitable user for the system to use, and will need to create the collections for the system.

The definition of the user will be:

```
db.createUser(
  {
    user: "imageuser",
    pwd: "your_password_goes_here",
    roles: [ { role: "readWrite", db: "imagetrack_database" } ]
  }
)
```

To create the collections you can use ```mongosh``` as a user with root level access (or ```DBAdmin``` on the ```imagetrack_database```).

```
use imagetrack_database
db.createCollection("projects_collection")
db.createCollection("people_collection")
db.createCollection("configuration_collection")
```

Create a master configuration file
==================================

Finally you need to create a local configuration file to give the details of the database and the data folder to the system.

Inside the imagetrack install folder you will find a folder called ```Configuration``` and inside there is a template file called ```example_conf.json```.  You need to make a copy of this called just ```conf.json```

```
cp example_conf.json conf.json
```

You then need to edit ```conf.json``` to add the details of the database connection and the data folder mount point.  This should then put the system into a working state.









