# Instructions for creating VENV and launching the app

python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux
. /venv/Scripts/activate

# Windows
# Get the python-ldap wheel file from https://www.lfd.uci.edu/~gohlke/pythonlibs/
pip3 install C:\Users\andrewss\Desktop\python_ldap-3.4.0-cp39-cp39-win_amd64.whl

# Linux
# install openldap-devel
pip3 install python-ldap

pip3 install flask bcrypt pymongo

# Debug
flask --app imagetrack_server run --debug
