#!/usr/bin/env python3

import requests 
import json
import sys
import os
sys.path.append("..") # Adds higher directory to python modules path.
import cloud_functions

print("\n\nParsing config file...")
data,file_name = cloud_functions.read_yml_file("config_flow",sys.argv,2,2)
            
# Get Default Home Dashboard
# url = f"http://{str(data['grafanaHostIP'])}:{str(data['grafanaPort'])}/api/dashboards/db"
url = f"{str(data['grafana_host'])}/api/dashboards/db"

# HTTP Post Header
# Replace with your Grafana API key
headers = {"Authorization": str(data['grafana_api_token']), 
           "Content-Type": "application/json",
            "Accept": "application/json"}

# Open and load out.json input
f = open(sys.argv[1],)
x = json.load(f)

# HTTP Post Request
r = requests.post(url=url, headers=headers, data=json.dumps(x), verify=False)
print(r.json())
