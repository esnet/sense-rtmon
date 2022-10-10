#!/usr/bin/env python3

import requests 
import json
import sys
import yaml
import os

owd = os.getcwd()
os.chdir("..")
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config_flow"
os.chdir(owd)
data = {}

# given config file
file_name = str(sys.argv[3])
file_path = config_path + "/" + file_name
print(f"\n Config file {file_path}\n")
with open(file_path, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(f"\n Config file {file_path} could not be found in the config directory\n")
            
# Get Default Home Dashboard
url = f"http://{str(data['grafanaHostIP'])}:{str(data['grafanaPort'])}/api/dashboards/db"

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