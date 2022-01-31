#!/usr/bin/env python3
from asyncio.windows_events import NULL
import json
import bcrypt
import random
from pymongo import MongoClient
from datetime import datetime
import cgi
import cgitb
cgitb.enable()

def main():
    # Set up the database connection
    client = MongoClient()
    db = client.imagetrack_database
    global projects
    global people
    global configuration
    projects = db.projects_collection
    people = db.people_collection
    configuration = db.configuration_collection
    
    form = cgi.FieldStorage()

    if not "action" in form:
        print("Content-type: text/plain; charset=utf-8\n\nNo action")
        return

    if form["action"].value == "login":
        process_login(form["email"].value,form["password"].value)

    elif form["action"].value == "configuration":
        get_configuration()

    else:
        # Everything else needs validation so let's check that first
        person = checksession(form["sessionid"].value)
        if person is None:
            send_response("Fail: Unknown session")
        
        if form["action"].value == "list_projects":
            get_projects(person["_id"])

        elif form["action"].value == "new_project":
            new_project(form)

def send_response(message):
    print("Content-type: text/plain; charset=utf-8\n\n"+message, end="")

def get_projects(personid):
    projects.find({"person_id"},personid)


def get_configuration():
    configuration.find_one()

def process_login (email,password):
    person = people.find_one({"email":email})

    # Check the password
    if bcrypt.checkpw(password,person["password"]):
        sessioncode = generate_id(20)
        people.update_one({{"email":email},{"sessioncode": sessioncode}})

        send_response("Success: "+sessioncode)
    else:
        send_response("Fail")


def checksession (sessioncode):
    person = people.find_one({"sessioncode":sessioncode})

    if person:
        return person["_id"],person["is_admin"]

    return None


def new_project(form):
    """
    Creates a new event and puts it into the database
    """

    project = {
    }

    projects.insert_one(project)

    send_response("Success")


def generate_id(size):
    """
    Generic function used for creating IDs
    """
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    code = ""

    for _ in range(size):
        code += random.choice(letters)

    return code




if __name__ == "__main__":
    main()