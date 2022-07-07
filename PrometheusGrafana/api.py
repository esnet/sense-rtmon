#!/usr/bin/env python3

import requests 
import json
import sys
import yaml
import os

owd = os.getcwd()
os.chdir("..")
infpth = str(os.path.abspath(os.curdir)) + "/config.yml"
os.chdir(owd)
data = {}
with open(infpth, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        pass

# http or https depending on Grafana setting
# if data['encrypted']:
server = "https://" + str(data['grafanaHostIP']) + ":" + str(data['grafanaPort'])
# else:
#     server = "http://" + str(data['grafanaHostIP']) + ":" + str(data['grafanaPort'])
    
# Get Default Home Dashboard
url = server + "/api/dashboards/db"
# HTTP Post Header
# Replace with your Grafana API key
headers = {"Authorization": str(data['grafanaAPIToken']),
            "Content-Type": "application/json",
            "Accept": "application/json"}
# Open and load out.json input
f = open(sys.argv[1],)
f2 = open(sys.argv[2],)
x = json.load(f)
x2 = json.load(f2)
# HTTP Post Request
r = requests.post(url=url, headers=headers, data=json.dumps(x), verify=False)
print(r.json())
r2 = requests.post(url=url, headers=headers, data=json.dumps(x2), verify=False)
print(r2.json())
