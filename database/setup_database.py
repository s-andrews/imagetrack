#!/usr/bin/env python3
import json
import bcrypt
from pymongo import MongoClient

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

    # Remove everything so we're starting fresh
    people.delete_many({})
    projects.delete_many({})
    configuration.delete_many({})

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

    # Add the configuration
    config = {
        "instruments":[
            "Zeiss 780 confocal",
            "Leica Stellaris 8 confocal",
            "Nikon A1-R confocal",
            "Olympus SpinSR spinning disk confocal",        
            "Olympus cellSens wide-field",
            "Nikon wide-field#1",
            "Nikon wide-field#2",
            "Nikon SIM/STORM/TIRF",
            "Zeiss MicroBeam laser-disssection",
            "Zeiss multi-photon",
            "MD/GE InCell 6000 high content"
        ],
        "modalities":[
            "Wide-field fluorescence",
            "Brightfield/transmitted light",
            "Differential Interference Contrast (DIC)",
            "Point-scanning confocal",
            "Spinning disk confocal",
            "Multi-photon",
            "SIM super resolution",
            "STORM super resolution",
            "High content",
            "Ultra-high content",
            "Laser microdissection/laser capture",
            "Total internal reflection fluorescence (TIRF)",
            "Fluorescence correlation spectroscopy (FCS)",
            "Fluorescence lifetime (FLIM)",
            "Forster Resonance Energy Transfer (FRET)"
        ],
        "groups":[
            "Kelsey",
            "Christophorou",
            "Houseley",
            "Howard",
            "Rayon",
            "Reik",
            "Rugg-Gunn",
            "Schoenfelder",
            "Tefely",
            "Voigt",
            "Turner",
            "Corcoran",
            "Linterman",
            "Liston",
            "Ribeiro de Almeida",
            "Richard",
            "Ross",
            "Cook",
            "Florey",
            "Hawkins",
            "Ktistakis",
            "McGough",
            "O'Donnell",
            "Rayon",
            "Samant",
            "Sharpe",
            "Stephens",
            "Welch",
            "David"
        ],

        "organisms" : [
            "Human (Homo sapiens)",
            "Mouse (Mus musculus)",
            "Rat (Rattus norvegicus)",
            "Fly (Drosophila melanogaster",
            "Worm (Caenorhabditis elegans)",
            "E.coli"
        ],

        "tags": [
            "Cell Type",
            "Cell Prep",
            "Fixation Method",
            "Primary Antibody",
            "Secondary Antibody",
            "Fluorescence Labels",
            "Passage Number",
            "Age",
            "Sex"
        ]
    }
    configuration.insert_one(config)

if __name__ == "__main__":
    main()