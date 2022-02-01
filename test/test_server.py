from distutils.command.config import config
import mechanize
from urllib.parse import urlencode
from bson.json_util import loads

def main():

    br = mechanize.Browser()

    # Check the root (should fail with no action)
    print("Testing root")
    answer = make_request(br,{})
    assert answer=="Fail: No Action"

    # Check the config
    print("Testing config")
    answer = make_request(br,{
        "action":"configuration"
    })
    configuration = loads(answer)
    assert("instruments" in configuration)
    assert("modalities" in configuration)
    assert("groups" in configuration)
    assert("organisms" in configuration)

    # Check login
    print("Testing login")
    answer = make_request(br,{
        "action":"login",
        "email":"simon.andrews@babraham.ac.uk",
        "password":"testing"})
    assert(answer.startswith("Success"))

    session = answer.split(" ")[1]

    # Create new user
    answer = make_request(br,{
        "action": "new_user",
        "session": session,
        "first_name": "Hanneke",
        "last_name": "Okkenhaug",
        "email": "hanneke.okkenhaug@babraham.ac.uk",
        "group": "imaging",
        "admin": False,
        "password": "testing2"
    })
    assert(answer.startswith("Success"))


    # Create a project
    print("Testing project creation")
    answer = make_request(br,{
        "action": "new_project",
        "session": session,
        "name": "Test Project",
        "instrument": configuration["instruments"][0],
        "modality": configuration["modalities"][0],
        "cell_type": "ES Cells",
        "cell_prep": "fixed",
        "fixation_method": "freezing",
        "primary_antibody": "nanog",
        "secondary_antibody": "IgG",
        "fluorescence_labels": None,
        "passage_number": 8,
        "organism": configuration["organisms"][0],
        "age": "d10",
        "sex": "male"})
    assert(answer.startswith("Success"))


    # List Projects
    print("Testing project listing")
    answer = make_request(br,{
        "action":"list_projects",
        "session": session
    })

    print(answer)
    projects = loads(answer)
    print(projects)

def make_request(br,params):
    base_url = "http://localhost:8000/cgi-bin/imagetrack_server.py"
    data = urlencode(params)
    response = br.open(base_url,data)
    return response.read().decode("UTF-8")

if __name__=="__main__":
    main()