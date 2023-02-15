#!/usr/bin/env python3

import requests 
import json
import sys
import yaml
import os
sys.path.append("..") # Adds higher directory to python modules path.
import cloud_functions

print("\n\nParsing config file...")
data,file_name = cloud_functions.read_yml_file("config_flow",sys.argv,3,2)
            
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
print(url)
r = requests.post(url=url, headers=headers, data=json.dumps(x), verify=False)
print(r.json())
print(url)
r2 = requests.post(url=url, headers=headers, data=json.dumps(x2), verify=False)
print(r2.json())