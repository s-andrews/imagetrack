#!/usr/bin/env python3
import json
import bcrypt
from pymongo import MongoClient
from pathlib import Path
from urllib.parse import quote_plus

def main():
    # Set up the database connection
    with open(Path(__file__).parent.parent / "Configuration/conf.json") as infh:
        conf = json.loads(infh.read())

    db_string = f"mongodb://{quote_plus(conf['username'])}:{quote_plus(conf['password'])}@{conf['server_address']}"
    print("Connecting to",db_string)
    client = MongoClient(db_string)
    db = client.imagetrack_database
    global projects
    global people
    projects = db.projects_collection
    people = db.people_collection

    # Remove everything so we're starting fresh
    people.delete_many({})
    projects.delete_many({})

    # Create an admin user
    admin = {
        "first_name": "Simon",
        "last_name": "Andrews",
        "email": "simon.andrews@babraham.ac.uk",
        "group": "bioinformatics",
        "admin": True,
        "password": bcrypt.hashpw("testing".encode("UTF-8"),bcrypt.gensalt()),
        "sessioncode": "",
        "reset_code": "",
        "shared_with": []
    }

    people.insert_one(admin)



if __name__ == "__main__":
    main()