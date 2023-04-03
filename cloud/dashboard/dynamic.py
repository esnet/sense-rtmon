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

# fill in the replacement dictionary of necessary values
def fill_rep(rep,id_num,node=None,iface=None):
    id_num += 1
    rep["YPOSITION"] = str(id_num)
    rep["PANELID"] = str(id_num)
    if node!=None:
        rep["NODENAME"] = node['name']
        rep["NODETYPE"] = node["type"].capitalize()
    if iface!=None:
        rep["IFNAME"] = iface['name']
        rep["IFVLAN"] = iface['vlan']
    return rep,id_num

def process_dict_list(dict_list):
    result = []
    for item in dict_list:
        item_str = []
        for key, value in item.items():
            if isinstance(value, list):
                value = ', '.join([f"{k}: {v}" for peer in value for k, v in peer.items()])
            item_str.append(f"{key}: {value}")
        result.append(" | ".join(item_str))
    
    result_str = "\\n".join(result)
    return result_str

#### parse file and general info ####
print("\n\nParsing config file...")
data,config_file = cloud_functions.read_yml_file("config_flow",sys.argv,1,2)
title = f'{data["title"]} |Flow: {data["flow"]}| {datetime.now().strftime("%m/%d_%H:%M")}'
push_metric = data['pushgateway'] # pushgateway metrics page

print("Process each node's information")
id_num = 200 # start from 200 in case of conflict with previous panels
for node in data["node"]:
    # write node info to a json file
    rep,id_num = fill_rep({},id_num,node)
    info_panel = replace_file_to_string("./templates/panel/info_panel.json",rep)
    concat_json(info_panel)
    
    # write interface to a json file
    rep,id_num = fill_rep(rep,id_num)
    rep["INTERFACEINFO"] = process_dict_list(node['interface'])
    interface_panel = replace_file_to_string("./templates/panel/interface_panel.json",rep)
    concat_json(interface_panel)
    
    for i,iface in enumerate(node['interface']):
        # special case host without ip address, no monitoring needed
        if 'ping' not in iface and node["type"] == "host":
            continue
        
        # write panel file
        rep,id_num = fill_rep(rep,id_num,node,iface)
        flow_panel = replace_file_to_string("./templates/panel/flow_panel.json",rep)
        
        # write target
        target_flow = replace_file_to_string(f"./templates/panel/flow_{node['type']}_target.json",rep)

        # write target to panel file
        flow_panel = flow_panel.replace("INSERTTARGET", target_flow)
        concat_json(flow_panel)    
        
        id_num += 1

# L2 debugging tables
id_num = id_num + 100 # L2 tables start from 100 after flow panels in case of conflict with previous panels

# write node info to a json file
rep,id_num = fill_rep({},id_num)
info_panel = replace_file_to_string("./templates/l2_debugging_panel/info_panel.json",rep)
concat_json(info_panel)
for i,node in enumerate(data["node"],i):
    # write table to a temp file
    rep,id_num = fill_rep({},id_num,node)
    l2table = replace_file_to_string("./templates/l2_debugging_panel/table.json",rep)

    formatted_name = node['name'].replace("-", "_").replace(".", "_").upper()
    for i in range(1,4):
        rep["NODENAME_SCRIPT_EXPORTER_TASK{i}"] = f"{formatted_name}SCRIPT_EXPORTER_TASK{i}"
    node_target = replace_file_to_string(f"./templates/l2_debugging_panel/{node['type']}_target.json",rep)
    
    l2table = l2table.replace("INSERTTARGET", node_target)
    concat_json(l2table)

# read the temp file and write to the all general dashboard template
dashboard_name = f"dash_{data['flow']}.json"
with open("./templates/temp.json") as file:
    all_panels = file.read()
    all_panels = all_panels[:-2] # remove the last comma and newline
    with open("./templates/general_dashboard.json") as infile, open(dashboard_name, 'w') as outfile:
        general_content = infile.read()
        general_content = general_content.replace("GRAFANAHOST",data["grafana_host"])
        general_content = general_content.replace("DASHTITLE",title)
        content = general_content.replace("INSERTALLPANELS",all_panels)
        outfile.write(content)

# remove temp file that's no longer needed
if os.path.exists("./templates/temp.json"):
    os.remove("./templates/temp.json")

# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py {dashboard_name} {config_file}"
subprocess.run(cmd, shell=True)