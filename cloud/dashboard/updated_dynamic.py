#!/usr/bin/env python3
import re
import sys
import subprocess
import os
from datetime import datetime
sys.path.append("..") # Adds higher directory to python modules path.
import cloud_functions

# This is a sandwich structure to build the json file
# General Dashboard Top         file_1
#   Panels                      file_2
#       Info Panel              file_3
#       Interface Panel         file_4
#           Interface targets   file_n
#   Dashboard Bottom            file_1
#
# Once Panels are built, they are added to the general dashboard template
# 1. write all interface targets inside the panels
# 2. write all the panels general dashboard template
# 3. write the general dashboard template to a unique flow file based on the flow ID given in config file 


# find the ifIndex of an interface on pushgateway site
def index_finder(name,pushgateway_metrics):
    cmd = f"curl {pushgateway_metrics} | tac | grep '.*ifName.*ifName=\"{name}\".*'"
    grep = subprocess.check_output(cmd,shell=True).decode()
    if_index = re.search('ifIndex="(.+?)\"',grep).group(1)
    return if_index

# read a file replace values then return the file in a string
def replace_file_to_string(file_name,replacements):
    with open(file_name) as file:
        content = file.read()
        for src, target in replacements.items():
            content = content.replace(str(src), str(target))
        return content
    
# concatenate to a json file
def concat_json(content,output="./templates/temp.json",end=False):
    if end == False:
        content = content + ",\n"
    with open(output, 'a') as outfile:
        outfile.write(content)   
          
def remove_file(file_path="./templates/temp.json"):
    if os.path.exists(file_path):
        os.remove(file_path)
    
#### parse file and general info ####
print("\n\nParsing config file...")
data,config_file = cloud_functions.read_yml_file("config_flow",sys.argv,1,2)
title = f'{data["title"]} |Flow: {data["flow"]}| {datetime.now().strftime("%m/%d_%H:%M")}'
general_rep = {}
general_rep["GRAFANAHOST"] = data["grafana_host"]
general_rep["DASHTITLE"] = title
push_metric = f"{data['pushgateway']}/metrics" # pushgateway metrics page

print("Process each node's information")
id_num = 200 # start from 200 in case of conflict with previous panels
for node in data["nodes"]:
    # write node info to a json file
    rep = {}
    rep["NODENAME"] = node['name']
    rep["NODETYPE"] = node["type"]
    rep["YPOSTION"] = str(id_num)
    rep["PANELID"] = str(id_num)
    info_panel = replace_file_to_string("./templates/info_panel.json",rep)
    concat_json(info_panel)
    
    # write interface to a json file
    id_num = id_num + 1
    rep["YPOSTION"] = str(id_num)
    rep["PANELID"] = str(id_num)
    rep["INTERFACEINFO"] = str(node['interface'])
    interface_panel = replace_file_to_string("./templates/interface_panel.json",rep)
    concat_json(interface_panel)
    
    for i,iface in enumerate(node['interface']):
        # special case host without ip address, no monitoring needed
        if 'ip' not in iface and node["type"] == "host":
            continue
        
        # write panel file
        id_num = id_num + 1
        rep["YPOSTION"] = str(id_num)
        rep["PANELID"] = str(id_num)
        rep["IFNAME"] = iface['name']
        rep["IFVLAN"] = iface['vlan']
        flow_panel = replace_file_to_string("./templates/flow_panel.json",rep)
        
        # find target
        if node["type"] == "switch":
            rep["DYNAMICIFINDEX"] = cloud_functions.index_finder(push_metric,iface['name'])    
        if 'ip' in iface:
            rep[f"IFIP"] = iface['ip']
        target_flow = replace_file_to_string(f"./templates/flow_{node['type']}_target.json",rep,end=True)

        # write target to panel file
        flow_panel = flow_panel.replace("INSERTTARGET", target_flow)

        # check if no more panels
        if i == len(node['interface'])-1:
            concat_json(flow_panel,end=True)    
        else:
            concat_json(flow_panel,end=False)    
        
        id_num += 1

# read the temp file and write to the all general dashboard template
dashboard_name = f"dash_{data['flow']}.json"
with open("./templates/temp.json") as file:
    all_panels = file.read()
    with open("./templates/general_dashboard.json") as infile, open(dashboard_name, 'w') as outfile:
        general_content = infile.read()
        content = general_content.replace("INSERTALLPANELS",all_panels)
        outfile.write(content)

# remove temp file that's no longer needed
if os.path.exists("./templates/temp.json"):
    os.remove("./templates/temp.json")

# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py {dashboard_name} {config_file}"
subprocess.run(cmd, shell=True)