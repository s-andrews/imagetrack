#!/usr/bin/env python3

from flask import Flask, jsonify, request, render_template
import bcrypt
import random
from pathlib import Path
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
import json
from urllib.parse import quote_plus
from datetime import date,datetime
import copy
import ldap

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/login", methods = ['POST', 'GET'])
def process_login():
    """
    Validates an username / password combination and generates
    a session id to authenticate them in future

    @username:  Their username (username for BI, email for external)
    @password:  The unhashed version of their password. Only used for externals

    @returns:   Forwards the session code to the json response
    """
    form = get_form()
    username = form["username"]
    password = form["password"]

    person = people.find_one({"username":username})

    # Check the password

    # If they just have a bare username then we validate against AD
    if not "@" in username:
        conn = ldap.initialize("ldap://babraham.ac.uk")
        conn.set_option(ldap.OPT_REFERRALS, 0)
        try:
            conn.simple_bind_s(username+"@babraham.ac.uk", password)
            sessioncode = generate_id(20)
            people.update_one({"username":username},{"$set":{"sessioncode": sessioncode}})

            return(sessioncode)
        
        except ldap.INVALID_CREDENTIALS:
          raise Exception("Incorrect Username/Password from LDAP")
        
    # If not then we hash their password and check it against the 
    # stored value
    else:
        if bcrypt.checkpw(password.encode("UTF-8"),person["password"]):
            sessioncode = generate_id(20)
            people.update_one({"username":username},{"$set":{"sessioncode": sessioncode}})

            return(sessioncode)
        else:
            raise Exception("Incorrect username/password from local password")

@app.route("/validate_session", methods = ['POST', 'GET'])
def validate_session():
    form = get_form()
    person = checksession(form["session"])
    return(person["admin"])

@app.route("/configuration")
def get_configuration():
    """
    Send the configuraton document, minus the server details

    @returns: The configuration document
    """

    config = copy.deepcopy(server_conf)
    config.pop("server",None)
    return jsonify(config)


@app.route("/list_people", methods = ['POST', 'GET'])
def list_people():
    """
    Gets the details of all users.  Only allowed to be called by
    admins.  Strips out the password and session details

    @person:   The person document for the person making the request

    @returns:  Forwards the people list to the json responder
    """
    form = get_form()
    person = checksession(form["sessionid"])

    if not person["admin"]:
        raise Exception("Only admins can do this")
        

    person_list = list(people.find({}))
    for person in person_list:
         person.pop("password",None)
         person.pop("sessioncode",None)
         person.pop("reset_code",None)

    return jsonify(person_list)



@app.route("/list_projects", methods = ['POST', 'GET'])
def list_projects():
    """
    Gets all projects associated with a given user

    @person:   The person document for the person making the request
    @user_oid: The oid of the user whose projects they want to see

    @returns:  Forwards the project list to the json responder
    """

    # We need to check that this person is allowed to view the
    # projects of the person they're requesting.
    # 
    # The easy check is that if it's their own projects or they
    # are an admin then it's all good.

    form = get_form()
    person = checksession(form["sessionid"])
    user_oid = form["user"]

    if person["admin"] or str(person["_id"]) == user_oid: 
        project_list = projects.find({"person_id":ObjectId(user_oid)})
        return jsonify(project_list)
    
    else:
        # TODO: Check for sharing permissions
        raise Exception("You can't look at this persons projects")


@app.route("/list_shared_users", methods = ['POST', 'GET'])
def list_shared_users():
    """
    Gets all the users who this user can see.  Everyone if they're an
    admin, or just people who have shared if they're a normal user

    @person:   The person document for the person making the request

    @returns:  Forwards the user list to the json responder
    """
   
    form = get_form()
    person = checksession(form["sessionid"])

    user_list = [person]

    if person["admin"]:
        user_list = people.find({})

    # TODO: Check for sharing permissions

    cut_down_user_list = []

    for u in user_list:
        cut_down_user_list.append({"_id":u["_id"],"first_name":u["first_name"],"last_name":u["last_name"]})

    return jsonify(cut_down_user_list)



@app.route("/project_details", methods = ['POST', 'GET'])
def project_details():
    """
    Retrieves a project document for a given oid

    @person:      The person document for the person making the request
    @oid:         The oid for the project
    @data_folder: The root directory for the data

    @returns:  Forwards the project document to the json responder
    """
    form = get_form()
    person = checksession(form["sessionid"])
    oid = form["oid"]

    # TODO: We could be fetching a project from another person
    # if this person is an admin.
    project_details = projects.find_one({"person_id":person["_id"], "_id":ObjectId(oid)})

    # We also need to get the list of files stored under this project
    # We'll end up summarising this in a few ways so we collect the 
    # raw data first.

    root_folder = Path(server_conf["data_folder"]) / project_details["folder"]

    file_tree, extension_details = collate_files(root_folder)

    project_details["files"] = file_tree
    project_details["extensions"] = extension_details

    return jsonify(project_details)

@app.route("/new_project", methods = ['POST', 'GET'])
def new_project():
    """
    Creates a new event and puts it into the database

    @person:  The hash of the person from the database
    @form:    The raw form from the CGI query
    @conf:    The configuration for the server to get the base dir for projects

    @returns: Forwards the new project document to the json responder
    """
    form = get_form()
    person = checksession(form["sessionid"])

    name = form["name"]
    instrument = form["instrument"]
    organism = form["organism"]
    modalities = form["modality"]

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

    real_folder = Path(server_conf["data_folder"])
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
                raise Exception("Couldn't find unused folder name")
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

    return jsonify(project)


@app.route("/new_person", methods = ['POST', 'GET'])
def new_person():
    """
    Creates or edits a user

    @person:   The person document for the person making the request
    @form:     The raw CGI form for the request

    @returns:  Sends a True value to the responder upon success
    """
    form = get_form()
    person = checksession(form["sessionid"])

    if not person["admin"]:
        raise Exception("Only Admins can make new users")

    # If they've supplied an oid then we're updating rather than creating
    oid = ""
    if "oid" in form and form["oid"]:
        oid = form["oid"]

    new_user = {
        "first_name": form["first_name"],
        "last_name": form["last_name"],
        "username": form["username"],
        "group": form["group"],
        "admin": form["admin"] == "true",
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
        if "@" in form["username"].value:
            new_user["password"] = bcrypt.hashpw(form["password"].value.encode("UTF-8"),bcrypt.gensalt())
        else:
            new_user["password"] = ""

        new_user["_id"] = people.insert_one(new_user).inserted_id
    
    return jsonify(new_user)
    

@app.route("/add_tag", methods = ['POST', 'GET'])
def add_tag():
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
    form = get_form()
    person = checksession(form["sessionid"])
    oid = form["oid"]

    doc = projects.find_one({"person_id":person["_id"], "_id":ObjectId(oid)})
    tags = doc["tags"]
    tags[form["tag_name"]] = form["tag_value"]

    projects.update_one({"_id":ObjectId(oid)},{"$set": {"tags":tags}})

    return(True)

@app.route("/remove_tag", methods = ['POST', 'GET'])
def remove_tag():
    """
    Removes a tag in an existing project.  

    @person:   The person document for the person removing the tag
    @oid:      The oid for the project
    @tag_name: The name of the tag

    @returns: Forwards a true value to the responder
    """
    form = get_form()
    person = checksession(form["sessionid"])
    oid = form["oid"]

    doc = projects.find_one({"person_id":person["_id"], "_id":ObjectId(oid)})
    tags = doc["tags"]

    del tags[form["tag_name"]]

    projects.update_one({"_id":ObjectId(oid)},{"$set": {"tags":tags}})

    return(True)


@app.route("/add_comment", methods = ['POST', 'GET'])
def add_comment():
    """
    Adds a comment to an existing project

    @person: The person document for the person adding the comment
    @oid:    The oid for the project
    @text:   The text of the comment

    @returns: Forwards a true value to the responder
    """
    form = get_form()
    person = checksession(form["sessionid"])
    oid = form["oid"]

    doc = projects.find_one({"person_id":person["_id"], "_id":ObjectId(oid)})
    comments = doc["comments"]
    comments.append({"date":str(datetime.now().replace(microsecond=0)), "text":form["text"]})

    projects.update_one({"_id":ObjectId(oid)},{"$set": {"comments":comments}})

    return(True)

def get_form():
    if request.method == "GET":
        return request.args

    elif request.method == "POST":
        return request.form


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

def checksession (sessioncode):
    """
    Validates a session code and retrieves a person document

    @sessioncode : The session code from the browser cookie

    @returns:      The document for the person associated with this session
    """

    person = people.find_one({"sessioncode":sessioncode})

    if person:
        return person

    raise Exception("Couldn't validate session")


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


# Read the main configuration
server_conf = get_server_configuration()

# Connect to the database
connect_to_database(server_conf)
