#!/usr/bin/env python3
import re
import sys
import subprocess
import os
from datetime import datetime
sys.path.append("..") # Adds higher directory to python modules path.
import cloud_functions

# parse file and general info
print("\n\nParsing config file...")
data,file_name = cloud_functions.read_yml_file("config_flow",sys.argv,1,2)
rep = cloud_functions.replacement_template() # rep for replacements
title = data["title"] + cloud_functions.make_title(data)
push_metric = f"{data['host_ip']}:9091/metrics" # pushgateway metrics page
rep["GRAFANAHOST"] = data['host_ip']
rep["DASHTITLE"] = title

# process host
print("Process Host Information")
host_num = data['host']['num']
host_if_vlan = []
for i in range(host_num):
    j = i+1 # j is 1 instead of 0 
    rep[f"IPHOST{j}"] = data[f"host{j}"]["ip"]
    rep[f"VLAN{j}"] = data[f"host{j}"]["vlan"]
    rep[f"IFNAMEHOST{j}"] = data["host{j}"]["interface"]
    rep[f"DATAPLANEIP{j}"] = data[f"host{j}"]["interface_ip"]
    rep[f"NODENAME{j}"] = data[f"host{j}"]["node"]
    rep[f"IFINDEXSWITCHHOST{j}"] = cloud_functions.index_finder(push_metric,data[f"host{j}"]["port{j}"]["ifName"])

# process switch SNMP needs to be run first
print("Process Switch Information")
print("find correct index from snmp exporter\n\n")
switch_num = data['switch']['num']
for i in range(host_num):
    j = i+1 # j is 1 instead of 0 
    rep[f"IPSWITCH{j}"] = data[f"switch{j}"]["target"]
    rep[f"SNMP{j}NAME"]= data[f"switch{j}"]["institute"]
    rep[f"SNMP{j}HOSTIP"] = data[f"switch{j}"]["running_from_ip"]
    
    num_port = data[f"switch{j}"]["num_port"]
    for k in range(num_port):
        l = k+1 # l is 1 instead of 0
        rep[f"SWITCH{j}PORT{l}IF"] = data[f"switch{j}"][f"port{l}"]["if_name"]
        rep[f"SWITCH{j}PORT{l}VLAN"]= data[f"switch{j}"][f"port{l}"]["vlan"]
        rep[f"IFINDEXSWITCH{j}PORT{l}"] = cloud_functions.index_finder(push_metric,data[f"switch{j}"][f"port{l}"]["if_name"])

# replacing
cloud_functions.replacing_json(f"./templates/future_proof.json","out.json",data,rep)

# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py out.json outDebug.json {file_name}"
subprocess.run(cmd, shell=True)
