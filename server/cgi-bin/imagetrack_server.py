#!/usr/bin/env python3
from pickletools import read_float8
import bcrypt
import random
from pathlib import Path
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
import json
from urllib.parse import quote_plus
from datetime import date,datetime
import cgi
import cgitb
cgitb.enable()

def main():
    # Read the main configuration
    server_conf = get_server_configuration()

    # Connect to the database
    connect_to_database(server_conf)
    
    # Collect the CGI connection fields
    form = cgi.FieldStorage()

    # Check the action and dispatch to the appropriate function
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
            project_details(person,form["oid"].value)

        elif form["action"].value == "new_project":
            new_project(person,form,server_conf)

        elif form["action"].value == "new_user":
            new_user(person,form)

        elif form["action"].value == "add_tag":
            add_tag(person,form["oid"].value,form["tag_name"].value,form["tag_value"].value)

        elif form["action"].value == "add_comment":
            add_comment(person,form["oid"].value,form["comment_text"].value)


def get_server_configuration():
    with open(Path(__file__).parent.parent.parent / "Configuration/conf.json") as infh:
        conf = json.loads(infh.read())
    return conf

def connect_to_database(conf):
    db_string = f"mongodb://{quote_plus(conf['username'])}:{quote_plus(conf['password'])}@{conf['server_address']}"
    client = MongoClient(db_string)

    db = client.imagetrack_database
    global projects
    global people
    global configuration
    projects = db.projects_collection
    people = db.people_collection
    configuration = db.configuration_collection


def send_response(success,message):
    if success:
        print("Content-type: text/plain; charset=utf-8\n\nSuccess: "+message, end="")
    else:
        print("Content-type: text/plain; charset=utf-8\n\nFail: "+message, end="")

def send_json(data):
    print("Content-type: text/json; charset=utf-8\n\n"+dumps(data))

def new_user(person,form):
    """
    Creates a new user

    @person:   The person document for the person making the request
    @form:     The raw CGI form for the request

    @returns:  Sends a True value to the responder upon success
    """
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
    """
    Gets all projects associated with a given user

    @person:   The person document for the person making the request

    @returns:  Forwards the project list to the json responder
    """
    project_list = projects.find({"person_id":person["_id"]})
    send_json(project_list)


def project_details(person,oid):
    """
    Retrieves a project document for a given oid

    @person:   The person document for the person making the request
    @oid:      The oid for the project

    @returns:  Forwards the project document to the json responder
    """
    project_details = projects.find_one({"person_id":person["_id"], "_id":ObjectId(oid)})
    send_json(project_details)


def add_tag(person,oid,tag_name, tag_value):
    """
    Adds or replaces a tag in an existing project.  Will define a new
    tag if it doesn't exist or will update the value of an existing
    tag.

    @person:   The person document for the person adding the comment
    @oid:      The oid for the project
    @tag_name: The name of the tag
    @tag_name: The text value for the tag

    @returns: Forwards a true value to the responder
    """

    doc = projects.find_one({"person_id":person["_id"], "_id":ObjectId(oid)})
    tags = doc["tags"]
    tags[tag_name] = tag_value

    projects.update_one({"_id":ObjectId(oid)},{"$set": {"tags":tags}})

    send_response(True,"")


def add_comment(person,oid,text):
    """
    Adds a comment to an existing project

    @person: The person document for the person adding the comment
    @oid:    The oid for the project
    @text:   The text of the comment

    @returns: Forwards a true value to the responder
    """
    doc = projects.find_one({"person_id":person["_id"], "_id":ObjectId(oid)})
    comments = doc["comments"]
    comments.append({"date":str(datetime.now().replace(microsecond=0)), "text":text})

    projects.update_one({"_id":ObjectId(oid)},{"$set": {"comments":comments}})

    send_response(True,"")



def get_configuration():
    """
    Retrieve the configuration document from the database

    @returns: The configuration document
    """

    config = configuration.find_one({})
    send_json(config)

def process_login (email,password):
    """
    Validates an email / password combination and generates
    a session id to authenticate them in future

    @email:     Their email (username)
    @password:  The unhashed version of their password

    @returns:   Forwards the session code to the json response
    """

    person = people.find_one({"email":email})

    # Check the password
    if bcrypt.checkpw(password.encode("UTF-8"),person["password"]):
        sessioncode = generate_id(20)
        people.update_one({"email":email},{"$set":{"sessioncode": sessioncode}})

        send_response(True,sessioncode)
    else:
        send_response(False,"Incorrect login")


def checksession (sessioncode):
    """
    Validates a session code and retrieves a person document

    @sessioncode : The session code from the browser cookie

    @returns:      The document for the person associated with this session
    """

    person = people.find_one({"sessioncode":sessioncode})

    if person:
        return person

    return None


def new_project(person,form,conf):
    """
    Creates a new event and puts it into the database

    @person:  The hash of the person from the database
    @form:    The raw form from the CGI query
    @conf:    The configuration for the server to get the base dir for projects

    @returns: Forwards the new project document to the json responder
    """

    name = form["name"].value
    instrument = form["instrument"].value
    organism = form["organism"].value
    modalities = form.getlist("modality[]")

    # We need to make up a new folder address for this project.
    # The structure of the address will be:

    # Base folder / Group / Person / date+name

    # Since the path to the root folder may not be the same on
    # all machines we store two versions of the folder location
    # A real one which is where the folder is located on the 
    # computer running the back end for the web system, and a 
    # virtual one which is a relative path from wherever the
    # root folder is.  On a given machine we can then modify
    # the displayed path to reflect the location of the folder
    # on that machine.

    real_folder = Path(conf["data_folder"])
    virtual_folder = Path(".")

    folders = [person["group"],person["first_name"]+person["last_name"],str(date.today())+"_"+name]

    bad_chars = "#%&{}\\\/<>*?$!'\":+`|="

    for f in folders:
        for c in bad_chars:
            f = f.replace(c,"_")

        real_folder = real_folder.joinpath(f)
        virtual_folder = virtual_folder.joinpath(f)
        
    # Make the new folder
    real_folder.mkdir(parents=True)

    project = {
        "person_id": person["_id"],
        "date": str(datetime.now().replace(microsecond=0)),
        "folder": str(virtual_folder),
        "name": name,
        "instrument": instrument,
        "modality": modalities,
        "organism": organism,
        "tags": {},
        "comments": []
    }

    project["_id"] = projects.insert_one(project).inserted_id

    send_json(project)


def generate_id(size):
    """
    Generic function used for creating IDs.  Makes random IDs
    just using uppercase letters

    @size:    The length of ID to generate

    @returns: A random ID of the requested size
    """
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    code = ""

    for _ in range(size):
        code += random.choice(letters)

    return code




if __name__ == "__main__":
    main()