import mechanize

base_url = "http://localhost:8000/cgi-bin/imagetrack_server.py"

br = mechanize.Browser()

# Check the root (should fail with no action)
answer = br.open(base_url)
assert answer.read().decode("UTF-8")=="Fail: No Action"

