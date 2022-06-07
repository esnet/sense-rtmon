#!/usr/bin/env python3

import requests 
import json
import sys
import yaml

data = {}
with open(sys.argv[2], 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        pass
# http or https check your Grafana setting
server = "https://" + str(data['grafanaHostIP']) + ":" + str(data['grafanaPort'])
# Get Default Home Dashboard
url = server + "/api/dashboards/db"
# HTTP Post Header
# Replace with your Grafana API key
headers = {"Authorization": str(data['grafanaAPIToken']),
            "Content-Type": "application/json",
            "Accept": "application/json"}
# Open and load out.json input
f = open(sys.argv[1],)
x = json.load(f)
# HTTP Post Request
r = requests.post(url=url, headers=headers, data=json.dumps(x), verify=False)
print(r.json())
