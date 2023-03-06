#!/usr/bin/env python3
import re
import sys
import subprocess
import os
from datetime import datetime
sys.path.append("..") # Adds higher directory to python modules path.
import cloud_functions

def index_finder(name,pushgateway_metrics):
    cmd = f"curl {pushgateway_metrics} | tac | grep '.*ifName.*ifName=\"{name}\".*'"
    grep = subprocess.check_output(cmd,shell=True).decode()
    if_index = re.search('ifIndex="(.+?)\"',grep).group(1)
    return if_index

#### parse file and general info ####
print("\n\nParsing config file...")
data,file_name = cloud_functions.read_yml_file("config_flow",sys.argv,1,2)
rep = {}
title = f'{data["title"]} |Flow: {data["flow"]}| {datetime.now().strftime("%m/%d_%H:%M")}'
rep["GRAFANAHOST"] = data["grafana_host"]
rep["DASHTITLE"] = title
push_metric = f"{data['pushgateway']}/metrics" # pushgateway metrics page

print("Process each node's information")
num_host = 0
num_switch = 0
i = 0
if_ind = 0
for node in data["nodes"]:
    rep[f"NODENAME{i}"] = node['name']
    for iface in node['interface']:
        rep[f"IFNAME{if_ind}"] = iface['name']
        rep[f"IFVLAN{if_ind}"] = iface['vlan']
        rep[f"IFINDEX{if_ind}"] = cloud_functions.index_finder(push_metric,iface['name'])
        if_ind += 1
        if 'ip' in iface:
            rep[f"IFIP{if_ind}"] = iface['ip']
        

    # if node["type"] == "host":
    #     make template and add the code for that section 
                
    # if node["type"] == "switch":
    #     make template and add the code for that section 

    i += 1

# replacing
with open(f"./templates/{data['flow']}.json") as infile, open(f"{data['flow']}]", 'w') as outfile:
    for line in infile:
        for src, target in rep.items():
            # target = str(target)
            line = line.replace(str(src), str(target))
        outfile.write(line)
        
# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py out.json {file_name}"
subprocess.run(cmd, shell=True)