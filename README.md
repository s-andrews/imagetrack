Image Track
===========

This is the code for the LIMS system we use to manage imaging data from the range of instruments we have in the imaging facility.  It's a relatively lightweight system which simply records a set of metadata from different imaging projects and then creates a structured system of folders under which the data from different projects can then be stored.

There are no restrictions on read/write access to the data on the imaging systems so this system operates on trust at the point of project creation, however we can potentially incorporate the information in this system into our virtual filesystem on the cluster so we can provide wider controlled access to the data once the projects are created.

Installing and Running
======================

Create the database
-------------------

You need to have a back end database set up on a mongodb server.  You will need to supply the 
host of the database as well as the name of the database and a username and password to access
it.


Install the App
---------------

This is a flask application.  You can in theory run it under windows or linux.  The instructions
here are for linux.

Start by cloning this repository onto the server you want to use.  It can be anywhere but we 
suggest putting it under ```/srv```

```
git clone https://github.com/s-andrews/imagetrack.git
```

Next you need to set up the virtual environment in which to run the app.  In order to install 
the python packages you might need to install some operating system packages (definintely 
openldap-devel but possibly others too).

```
cd imagetrack/server/flask

python3 -m venv venv
. venv/bin/activate
pip3 install flask python-ldap bcrypt

```

Create the config file
======================

The main configuration for the site is in ```Configuration/conf.json``` and you will need to
create this file.  There is an example file in ```Configuration/example_conf.json``` which you
can copy and edit.

Populate the database
=====================

We need to create an initial user to be able to use the site.  The script to do this is
```Configuration/setup_database.py```.  Inside the script there is a json section with the 
details of the admin user you intially want to create and you can edit these to whatever
name and username you like.  Once you're happy then initialise the venv and run:

```
python3 setup_database.py
```

..from within the ```Configuration``` folder.


Install the apache configuration
================================

The default apache configuration proxies the flask server to ```/imaging/``` on your server.

```
cd /etc/httpd/conf.d/
sudo ln -s /srv/imagetrack/Configuration/imagretrack_apache.conf .

systemctl restart httpd
```

Start the App
=============

```
cd /srv/imagetrack/server/flask

. venv/bin/activate

nohup flask --app imagetrack run & > /dev/null
```

Your app should now appear at ```http://yourserver/imaging/```


