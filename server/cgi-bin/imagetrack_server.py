#!/usr/bin/env python3
from msilib.schema import Error
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
import copy
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
        send_response(True,person["admin"])


    elif form["action"].value == "configuration":
        get_configuration(server_conf)

    else:
        # Everything else needs validation so let's check that first
        person = checksession(form["session"].value)
        if person is None:
            send_response(False,"Unknown session")
        
        elif form["action"].value == "list_people":
            list_people(person)

        elif form["action"].value == "list_projects":
            list_projects(person)

        elif form["action"].value == "project_details":
            project_details(person,form["oid"].value, server_conf["server"]["data_folder"])

        elif form["action"].value == "new_project":
            new_project(person,form,server_conf["server"]["data_folder"])

        elif form["action"].value == "new_person":
            new_person(person,form)

        elif form["action"].value == "add_tag":
            add_tag(person,form["oid"].value,form["tag_name"].value,form["tag_value"].value)

        elif form["action"].value == "add_comment":
            add_comment(person,form["oid"].value,form["comment_text"].value)


def get_server_configuration():
    with open(Path(__file__).parent.parent.parent / "Configuration/conf.json") as infh:
        conf = json.loads(infh.read())
    return conf

def connect_to_database(conf):
    db_string = f"mongodb://{quote_plus(conf['server']['username'])}:{quote_plus(conf['server']['password'])}@{conf['server']['address']}"
    client = MongoClient(db_string)

    db = client.imagetrack_database

    global projects
    global people
    projects = db.projects_collection
    people = db.people_collection


def send_response(success,message):
    if success:
        print("Content-type: text/plain; charset=utf-8\n\nSuccess: "+str(message), end="")
    else:
        print("Content-type: text/plain; charset=utf-8\n\nFail: "+str(message), end="")

def send_json(data):
    print("Content-type: text/json; charset=utf-8\n\n"+dumps(data))

def new_person(person,form):
    """
    Creates or edits a user

    @person:   The person document for the person making the request
    @form:     The raw CGI form for the request

    @returns:  Sends a True value to the responder upon success
    """
    if not person["admin"]:
        send_response(False,"Only Admins can make new users")

    # If they've supplied an oid then we're updating rather than creating
    oid = ""
    if "oid" in form and form["oid"].value:
        oid = form["oid"].value

    new_user = {
        "first_name": form["first_name"].value,
        "last_name": form["last_name"].value,
        "email": form["email"].value,
        "group": form["group"].value,
        "admin": form["admin"].value == "true",
        "sessioncode": None,
        "reset_code": None,
        "shared_with": []
    }

    if oid:
        existing_user = people.find_one({"_id": ObjectId(oid)})
        # We need to copy over the sessioncode from the
        # old entry, as well as the password if they 
        # haven't reset it
        new_user["_id"] = existing_user["_id"]
        new_user["sessioncode"] = existing_user["sessioncode"]
        new_user["reset_code"] = existing_user["reset_code"]
        new_user["sessioncode"] = existing_user["sessioncode"]
        new_user["shared_with"] = existing_user["shared_with"]

        if not ("password" in form and form["password"].value):
            new_user["password"] = existing_user["password"]
        else:
            new_user["password"] = bcrypt.hashpw(form["password"].value.encode("UTF-8"),bcrypt.gensalt())


        people.replace_one({"_id":new_user["_id"]},new_user)

    else:
        new_user["password"] = bcrypt.hashpw(form["password"].value.encode("UTF-8"),bcrypt.gensalt())

        new_user["_id"] = people.insert_one(new_user).inserted_id
    
    send_json(new_user)
    

def list_projects(person):
    """
    Gets all projects associated with a given user

    @person:   The person document for the person making the request

    @returns:  Forwards the project list to the json responder
    """
    project_list = projects.find({"person_id":person["_id"]})
    send_json(project_list)



def list_people(person):
    """
    Gets the details of all users.  Only allowed to be called by
    admins.  Strips out the password and session details

    @person:   The person document for the person making the request

    @returns:  Forwards the people list to the json responder
    """

    if not person["admin"]:
        send_response(False, "Only admins can do this")
        return

    person_list = list(people.find({}))
    for person in person_list:
         person.pop("password",None)
         person.pop("sessioncode",None)
         person.pop("reset_code",None)

    send_json(person_list)



def project_details(person,oid, data_folder):
    """
    Retrieves a project document for a given oid

    @person:      The person document for the person making the request
    @oid:         The oid for the project
    @data_folder: The root directory for the data

    @returns:  Forwards the project document to the json responder
    """
    project_details = projects.find_one({"person_id":person["_id"], "_id":ObjectId(oid)})

    # We also need to get the list of files stored under this project
    # We'll end up summarising this in a few ways so we collect the 
    # raw data first.

    root_folder = Path(data_folder) / project_details["folder"]

    file_tree, extension_details = collate_files(root_folder)

    project_details["files"] = file_tree
    project_details["extensions"] = extension_details

    send_json(project_details)

def collate_files(root_folder):
    """
    Iterates through a folder to get the full list of files and folders
    and their respective sizes

    @root_folder: The folder in which to profile things

    @returns: A tree structure with all of the file details
    """
    file_tree = {}
    extension_stats = {}

    for i in root_folder.rglob("*"):

        if i.is_file():
            suffix = i.suffix
            if suffix:
                suffix = suffix[1:]
                if not suffix in extension_stats:
                    extension_stats[suffix] = {"files":0, "size":0}
                
                extension_stats[suffix]["size"] += i.stat().st_size
                extension_stats[suffix]["files"] += 1



        parts = i.relative_to(root_folder).parts
        
        node = file_tree

        for part in parts:
            if not part in node:
                node[part] = {}
            
            node = node[part]


    # Now we need to turn the structure we have into something compatible with 
    # jstree
    def process_node(js,node):
        for i in node.keys():
            if not node[i]: # There's nothing under this so it's a file (TODO: Check!)
                js["children"].append({
                    "text": i,
                    "icon": "images/file.png",
                    "state": {
                        "opened": False,
                        "disabled": False,
                        "selected": False
                    },
                    "children": []
                })
            else:
                # It's a folder
                new_node = {
                    "text": i,
                    "icon": "images/folder.png",
                    "state": {
                        "opened": False,
                        "disabled": False,
                        "selected": False
                    },
                    "children": []
                }
                js["children"].append(new_node)

                process_node(new_node,node[i])
        
    js_tree = {"text": root_folder.name,
                "icon": "images/folder.png",
                "state": {
                    "opened": False,
                    "disabled": False,
                    "selected": False
                },
                "children": []}
    process_node(js_tree,file_tree)

    return(js_tree,extension_stats)

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


def get_configuration(server_conf):
    """
    Send the configuraton document, minus the server details

    @returns: The configuration document
    """

    config = copy.deepcopy(server_conf)
    config.pop("server",None)
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


def new_project(person,form,data_folder):
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

    real_folder = Path(data_folder)
    virtual_folder = Path(".")

    folders = [person["group"],person["first_name"]+person["last_name"],str(date.today())+"_"+name]

    bad_chars = "#%&{}\\\/<>*?$!'\":+`|="

    for f in folders:
        for c in bad_chars:
            f = f.replace(c,"_")

        real_folder = real_folder.joinpath(f)
        virtual_folder = virtual_folder.joinpath(f)
        
    # Check whether this folder exists already.  It might if they make multiple 
    # projects on the same day with the same name.  If it does we just append 
    # _001, _002 etc to the end until it's novel.

    if real_folder.exists():
        suffix = 1
        while True:
            if suffix == 100:
                raise Error("Couldn't find unused folder name")
            if not (real_folder.parent / (real_folder.name+"_"+str(suffix).zfill(3))).exists():
                real_folder = real_folder.parent / (real_folder.name+"_"+str(suffix).zfill(3))
                virtual_folder = virtual_folder.parent / (virtual_folder.name+"_"+str(suffix).zfill(3))
                break
        
            suffix += 1

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