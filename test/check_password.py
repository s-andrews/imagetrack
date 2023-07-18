import sys
import ldap
import getpass


Server = "ldap://babraham.ac.uk"
username = "andrewss@babraham.ac.uk"
password = getpass.getpass()

l = ldap.initialize(Server)
l.set_option(ldap.OPT_REFERRALS, 0)
try:
  l.simple_bind_s(username, password)
  print("Worked")
except ldap.INVALID_CREDENTIALS:
  print('wrong password provided')

sys.exit()