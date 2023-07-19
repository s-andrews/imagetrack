# Run these in a python shell to get a basically 
# functional db environment

import json
import bcrypt
from bson.objectid import ObjectId
from pymongo import MongoClient
from pathlib import Path
from urllib.parse import quote_plus
with open(Path(".") / "Configuration/conf.json") as infh:
    conf = json.loads(infh.read())

db_string = f"mongodb://{quote_plus(conf['server']['username'])}:{quote_plus(conf['server']['password'])}@{conf['server']['address']}"
client = MongoClient(db_string)
db = client.imagetrack_database
projects = db.projects_collection
people = db.people_collection

breakpoint()
