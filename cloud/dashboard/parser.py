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
rep["DASHTITLE"] = title
push_metric = f"{data['pushgateway']}/metrics" # pushgateway metrics page

rep["YPOSITION"] = str(10000+1)

# read a file replace values then return the file in a string
def replace_file_to_string(file_name,replacements):
    with open(file_name) as file:
        content = file.read()
        for src, target in replacements.items():
            content = content.replace(str(src), str(target))
        return content

def conat_json(content,output="./templates/temp.json",end=False):
    if end == False:
        content = content + ",\n"
    with open(output, 'a') as outfile:
        outfile.write(content)   

content = replace_file_to_string("./templates/info_panel.json",rep)
conat_json(content)
conat_json(content)


# print("Process each node's information")
# i = 0
# if_ind = 0
# for node in data["node"]:
#     rep[f"NODENAME{i}"] = node['name']
#     print(rep[f"NODENAME{i}"])
#     for iface in node['interface']:
#         rep[f"IFNAME{if_ind}"] = iface['name']
#         rep[f"IFVLAN{if_ind}"] = iface['vlan']
#         # rep[f"IFINDEX{if_ind}"] = cloud_functions.index_finder(push_metric,iface['name'])
#         print(rep[f"IFNAME{if_ind}"])
#         print(rep[f"IFVLAN{if_ind}"])
#         if_ind += 1
#         if 'ip' in iface:
#             rep[f"IFIP{if_ind}"] = iface['ip']
#             print(rep[f"IFIP{if_ind}"])
#     # if node["type"] == "host":
#     #     make template and add the code for that section 
                
#     # if node["type"] == "switch":
#     #     make template and add the code for that section 

#     i += 1

# print(rep)

# # replacing
# with open(f"./templates/{data['flow']}.json") as infile, open(f"{data['flow']}]", 'w') as outfile:
#     for line in infile:
#         for src, target in rep.items():
#             # target = str(target)
#             line = line.replace(str(src), str(target))
#         outfile.write(line)
        
# # Run the API script to convert output JSON to Grafana dashboard automatically
# cmd = f"sudo python3 api.py out.json {file_name}"
# subprocess.run(cmd, shell=True)