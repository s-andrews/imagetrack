#!/usr/bin/env python3

from flask import Flask, jsonify
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
    return("<p>LIMS</p>")

@app.route("/login")
def process_login():
    pass

@app.route("/validate_session")
def validate_session():
    pass

@app.route("/configuration")
def get_configuration():
    """
    Send the configuraton document, minus the server details

    @returns: The configuration document
    """

    config = copy.deepcopy(server_conf)
    config.pop("server",None)
    return jsonify(config)


@app.route("/list_people")
def list_people():
    pass

@app.route("/list_projects")
def list_projects():
    pass

@app.route("/list_shared_users")
def list_shared_users():
    pass

@app.route("/project_details")
def project_details():
    pass

@app.route("/new_project")
def new_project():
    pass

@app.route("/new_person")
def new_person():
    pass

@app.route("/add_tag")
def add_tag():
    pass

@app.route("/remove_tag")
def remove_tag():
    pass

@app.route("/add_comment")
def validate_session():
    pass

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

    return None


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
