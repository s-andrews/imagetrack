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
