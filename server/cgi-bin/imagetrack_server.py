#!/usr/bin/env python3
import bcrypt
import random
from pathlib import Path
from pymongo import MongoClient
from bson.json_util import dumps
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

    elif form["action"].value == "validate_session":
        person = checksession(form["session"].value)
        send_response(True,person["first_name"]+" "+person["last_name"])


    elif form["action"].value == "configuration":
        get_configuration()

    else:
        # Everything else needs validation so let's check that first
        person = checksession(form["session"].value)
        if person is None:
            send_response(False,"Unknown session")
        
        elif form["action"].value == "list_projects":
            list_projects(person)

        elif form["action"].value == "project_details":
            project_details(person,form["folder"].value)

        elif form["action"].value == "new_project":
            new_project(person,form)

        elif form["action"].value == "new_user":
            new_user(person,form)

        elif form["action"].value == "add_tag":
            add_tag(person,form["folder"].value,form["tag_name"].value,form["tag_value"].value)

        elif form["action"].value == "add_comment":
            add_comment(person,form["folder"].value,form["comment_text"].value)


def send_response(success,message):
    if success:
        print("Content-type: text/plain; charset=utf-8\n\nSuccess: "+message, end="")
    else:
        print("Content-type: text/plain; charset=utf-8\n\nFail: "+message, end="")

def send_json(data):
    print("Content-type: text/json; charset=utf-8\n\n"+dumps(data))

def new_user(person,form):

    if not person["admin"]:
        send_response(False,"Only Admins can make new users")

    new_user = {
        "first_name": form["first_name"].value,
        "last_name": form["last_name"].value,
        "email": form["email"].value,
        "group": form["group"].value,
        "admin": False,
        "password": bcrypt.hashpw(form["password"].value.encode("UTF-8"),bcrypt.gensalt()),
        "sessioncode": None,
        "reset_code": None,
        "shared_with": []
    }

    people.insert_one(new_user)

    send_response(True,"")
    

def list_projects(person):
    project_list = projects.find({"person_id":person["_id"]})
    send_json(project_list)


def project_details(person,folder):
    project_details = projects.find_one({"person_id":person["_id"], "folder":folder})
    send_json(project_details)


def add_tag(person,folder,tag_name, tag_value):
    doc = projects.find_one({"person_id":person["_id"], "folder":folder})
    tags = doc["tags"]
    tags[tag_name] = tag_value

    projects.update_one({"folder":folder},{"$set": {"tags":tags}})

    send_response(True,"")


def add_comment(person,folder,text):
    doc = projects.find_one({"person_id":person["_id"], "folder":folder})
    comments = doc["comments"]
    comments.append({"date":str(date.today()), "text":text})

    projects.update_one({"folder":folder},{"$set": {"comments":comments}})

    send_response(True,"")



def get_configuration():
    config = configuration.find_one({})
    send_json(config)

def process_login (email,password):
    person = people.find_one({"email":email})

    # Check the password
    if bcrypt.checkpw(password.encode("UTF-8"),person["password"]):
        sessioncode = generate_id(20)
        people.update_one({"email":email},{"$set":{"sessioncode": sessioncode}})

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

    name = form["name"].value
    instrument = form["instrument"].value
    organism = form["organism"].value
    modalities = form.getlist("modality[]")

    # We need to make up a new folder address for this project.
    # The structure of the address will be:

    # Base folder / Group / Person / date+name

    folder = Path("c:/Users/andrewss/")

    folders = [person["group"],person["first_name"]+person["last_name"],str(date.today())+"_"+name]

    # TODO: Remove invalid characters
    bad_chars = "#%&{}\\\/<>*?$!'\":+`|="

    for f in folders:
        for c in bad_chars:
            f = f.replace(c,"_")

        folder = folder.joinpath(f)
        
    project = {
        "person_id": person["_id"],
        "date": str(date.today()),
        "folder": str(folder),
        "name": name,
        "instrument": instrument,
        # TODO: Deal with multiple modalities
        "modality": modalities,
        "organism": organism,
        "tags": {},
        "comments": []
    }

    project["_id"] = projects.insert_one(project).inserted_id

    send_json(project)


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