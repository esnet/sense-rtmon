#!/usr/bin/env python3
import re
import sys
import subprocess
import os
from datetime import datetime
sys.path.append("..") # Adds higher directory to python modules path.
import cloud_functions

#### parse file and general info ####
print("\n\nParsing config file...")
data,file_name = cloud_functions.read_yml_file("config_flow",sys.argv,1,2)
rep = {}
title = data["title"] + cloud_functions.make_title(data)
push_metric = f"{data['pushgateway']}/metrics" # pushgateway metrics page
rep["GRAFANAHOST"] = data['host_ip']
rep["DASHTITLE"] = title

######## process host ########
print("Process Host Information")
host_if_vlan = []
for i in range(1,data['host']['num']+1):
    rep[f"IPHOST{i}"] = data[f"host{i}"]["ip"]
    rep[f"VLAN{i}"] = data[f"host{i}"]["vlan"]
    rep[f"IFNAMEHOST{i}"] = data["host{i}"]["interface"]
    rep[f"DATAPLANEIP{i}"] = data[f"host{i}"]["interface_ip"]
    rep[f"NODENAME{i}"] = data[f"host{i}"]["node"]
    rep[f"IFINDEXSWITCHHOST{i}"] = cloud_functions.index_finder(push_metric,data[f"host{i}"]["port{i}"]["ifName"])

#### process switch SNMP needs to be run first ####
print("Process Switch Information")
print("find correct index from snmp exporter\n\n")
for i in range(1,data['switch']['num']+1):
    rep[f"IPSWITCH{i}"] = data[f"switch{i}"]["target"]
    rep[f"SNMP{i}NAME"]= data[f"switch{i}"]["institute"]
    rep[f"SNMP{i}HOSTIP"] = data[f"switch{i}"]["running_from_ip"]
    
    for j in range(i,data[f"switch{i}"]["num_port"]+1):
        rep[f"SWITCH{i}PORT{j}IF"] = data[f"switch{i}"][f"port{j}"]["if_name"]
        rep[f"SWITCH{i}PORT{j}VLAN"]= data[f"switch{i}"][f"port{j}"]["vlan"]
        rep[f"IFINDEXSWITCH{i}PORT{j}"] = cloud_functions.index_finder(push_metric,data[f"switch{i}"][f"port{j}"]["if_name"])

# replacing
cloud_functions.replacing_json(f"./templates/future_proof.json","out.json",data,rep)

# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py out.json outDebug.json {file_name}"
subprocess.run(cmd, shell=True)