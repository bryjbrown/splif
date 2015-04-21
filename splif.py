#!/usr/bin/env python3

# Define acceptable status codes for Graduate Student and Faculty roles.
gradnums = [10, 11, 12, 15, 18, 19] # Graduate Students
facnums = [20, 21, 22, 28, 29] # Faculty

import sys
import re

if len(sys.argv) < 2:
  print("Error: No PLIF provided. Supply PLIF as arg 1.")
  sys.exit()

data = []
with open(sys.argv[1], encoding="ISO-8859-1") as f:
  for line in f:
    spline = re.split(r'\s{2,}', line)
    person = {}
    for cell in spline:

      status = re.compile(r'\d\d%')
      name = re.compile(r'A0102[a-zA-Z-\']+\s[a-zA-Z]+')
      email = re.compile(r'.*fsu\.edu$')
      
      if status.match(cell):
        person["status"] = cell

      if name.match(cell):
        fullname = cell.replace('A0102', '').split()
        person["firstname"] = fullname[1].replace("'", "\\'")
        person["lastname"] = fullname[0].replace("'", "\\'")

      if email.match(cell):
        person["email"] = cell
        username = cell.split("@")
        person["username"] = username[0]


    statuscode = int(person["status"].replace("%", ""))
    if statuscode in gradnums and "username" in person.keys():
      person["role"] = 'Graduate Student'
      data.append(person)
    elif statuscode in facnums and "username" in person.keys():
      person["role"] = 'Faculty'
      data.append(person)
    
output = open(sys.argv[1] + "-output.sh", "w")
output.seek(0)
header = """#!/bin/sh

# This script uses drush, so make sure to run it inside of a Drupal filesystem
# Configure vars to use database credentials (found in Drupal's settings.php)
dbhost=''
dbuser=''
dbpass=''
dbname=''
dbprefix=''

run_user () {
  drush user-information ${1} &>/dev/null
  if [ ${?} == 0 ]
  then
    echo "${1} exists"
  else
    echo "${1} doesn't exist, creating profile"
    drush cas-user-create ${1} &>/dev/null
    uid=`mysql -h ${dbhost} -u ${dbuser} -p${dbpass} ${dbname} -BN -e "select uid from ${dbprefix}users where name=\\"${1}\\";"`
    drush user-add-role "${2}" ${uid} &>/dev/null
    mysql -h ${dbhost} -u ${dbuser} -p${dbpass} ${dbname} -e "update ${dbprefix}users set mail=\\"${3}\\" where uid=\\"${uid}\\";"
    mysql -h ${dbhost} -u ${dbuser} -p${dbpass} ${dbname} -e "insert into ${dbprefix}field_data_field_first_name values ('user', 'user', 0, ${uid}, ${uid}, 'und', 0, '${4}', NULL);"
    mysql -h ${dbhost} -u ${dbuser} -p${dbpass} ${dbname} -e "insert into ${dbprefix}field_data_field_last_name values ('user', 'user', 0, ${uid}, ${uid}, 'und', 0, '${5}', NULL);"
  fi
}

"""
output.write(header)
    
for person in data:
  output.write("run_user {0} \"{1}\" \"{2}\" \"{3}\" \"{4}\"\n".format(person["username"], person["role"], person["email"], person["firstname"], person["lastname"]))

output.write("\necho \"Loading complete!\"")
output.close()

print("Done! Output can be found in {}-output.sh".format(sys.argv[1]))
print("This file should take ~{} hours to load".format(((len(data) / 60) / 60)))
print("Don't forget to configure the database connection vars!")


