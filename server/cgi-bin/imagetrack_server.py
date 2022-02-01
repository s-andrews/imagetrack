#!/usr/bin/env python3
from asyncio.windows_events import NULL
import json
import bcrypt
import random
from pymongo import MongoClient
from datetime import date
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
        send_response(False,"No Action")
        return

    if form["action"].value == "login":
        process_login(form["email"].value,form["password"].value)

    elif form["action"].value == "configuration":
        get_configuration()

    else:
        # Everything else needs validation so let's check that first
        person = checksession(form["sessionid"].value)
        if person is None:
            send_response(False,"Unknown session")
        
        elif form["action"].value == "list_projects":
            get_projects(person)

        elif form["action"].value == "new_project":
            new_project(person,form)

def send_response(success,message):
    if success:
        print("Content-type: text/plain; charset=utf-8\n\nSuccess: "+message, end="")
    else:
        print("Content-type: text/plain; charset=utf-8\n\nFail: "+message, end="")

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

        send_response(True,sessioncode)
    else:
        send_response(False,"Incorrect login")


def checksession (sessioncode):
    person = people.find_one({"sessioncode":sessioncode})

    if person:
        return person

    return None


def new_project(person,form):
    """
    Creates a new event and puts it into the database
    """

    # We need to make up a new folder address for this project.
    # The structure of the address will be:

    # Base folder / Group / Person / date+name

    folders = [person["group"],person["first_name"]+person["last_name"],str(date.today())+"_"+form["name"].value]

    # TODO: Remove invalid characters
    bad_chars = "#%&{}\\\/<>*?$!'\":+`|="

    valid_folders = []

    for folder in folders:
        for c in bad_chars:
            folder = folder.replace(c,"_")
        
        valid_folders.add(folder)


    project = {
        "person_id": person["_id"],
        "date": str(date.today()),
        "name": form["name"].value,
        "instrument": form["instrument"].value,
        "modality": ["Spinning disk confocal","Multi-photon"],
        "cell_type": form["cell_type"].value,
        "cell_prep": form["cell_prep"].value,
        "fixation_method": form["fixation_method"].value,
        "primary_antibody": form["primary_antibody"].value,
        "secondary_antibody": form["secondary_antibody"].value,
        "fluorescence_labels": form["fluorescence_labels"].value,
        "passage_number": form["passage_number"].value,
        "organism": form["organism"].value,
        "age": form["age"].value,
        "sex": form["sex"].value,
        "comments": []
    }

    id = projects.insert_one(project)

    send_response(True,id.inserted_id)


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