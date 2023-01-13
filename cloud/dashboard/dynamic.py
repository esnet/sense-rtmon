#!/usr/bin/env python3
import re
import yaml
import sys
import subprocess
import os
from datetime import datetime
sys.path.append("..") # Adds higher directory to python modules path.
import cloud_functions

print("\n\nParsing config file...")
data,file_name = cloud_functions.read_yml_file("config_flow",sys.argv,1,2)
switch_num = int(data['switchNum'])
print("find correct index from snmp exporter\n\n")
pushgateway_metrics = f"{data['hostIP']}:9091/metrics"

# holders for interface index
if_index1 = "IFINDEXSWITCHHOSTA"
if_index2 = "IFINDEXSWITCHHOSTB"


### commenting the below allows dashboard generation but the following are needed for SNMP monitoring ###

######################## COMMENTING FOR TESTING ########################

if_index1 = cloud_functions.index_finder(pushgateway_metrics,str(data["hostA"]["switchPort"]["ifName"]))
if_index2 = cloud_functions.index_finder(pushgateway_metrics,str(data["hostB"]["switchPort"]["ifName"]))

switch_if_index=[]

for i in range(switch_num):
    letter = chr(ord('A')+i) # A B C D ... 
    switch_if_index.append(cloud_functions.index_finder(pushgateway_metrics,str(data[f"switchData{letter}"]["portIn"]["ifName"])))
    switch_if_index.append(cloud_functions.index_finder(pushgateway_metrics,str(data[f"switchData{letter}"]["portOut"]["ifName"])))    

######################## COMMENTING FOR TESTING ########################

dash_title = data["dashTitle"] + cloud_functions.make_title(data)
debug_title = data["debugTitle"] + cloud_functions.make_title(data)
replacements = cloud_functions.replacement_template()
replacements["DASHTITLE"] = dash_title
replacements["DEBUGTITLE"] = debug_title
replacements["IPHOSTA"] = data["hostA"]["IP"]
replacements["IPHOSTB"] = data["hostB"]["IP"]
replacements["VLANA"] = data["hostA"]["vlan"]
replacements["VLANB"] = data["hostB"]["vlan"]
replacements["IFNAMEHOSTA"] = data["hostA"]["interfaceName"]
replacements["IFNAMEHOSTB"] = data["hostB"]["interfaceName"]
# switch 1
replacements["IFINDEXSWITCHHOSTA"] = if_index1
replacements["IFINDEXSWITCH1HOSTA"] = switch_if_index[0]
replacements["IFINDEXSWITCH1HOSTB"] = switch_if_index[1]
# switch 2
replacements["IFINDEXSWITCH2HOSTA"] = switch_if_index[2]
replacements["IFINDEXSWITCH2HOSTB"] = switch_if_index[3]
replacements["IFINDEXSWITCHHOSTB"] = if_index2

replacements["DATAPLANEIPA"] = data["hostA"]["interfaceIP"]
replacements["DATAPLANEIPB"] = data["hostB"]["interfaceIP"]
replacements["NODENAMEA"] = data["hostA"]["nodeName"]
replacements["NODENAMEB"] = data["hostB"]["nodeName"]

for i in range(switch_num):
    letter = chr(ord('A')+i) # A B C D ... 
    replacements[f"IPSWITCH{letter}"] = data[f"switchData{letter}"]["target"]
    replacements[f"SNMP{letter}NAME"]= data[f"switchData{letter}"]["job_name"]
    replacements[f"SWITCH{letter}INVLAN"]= data[f"switchData{letter}"]["portIn"]["vlan"]
    replacements[f"SWITCH{letter}OUTVLAN"]= data[f"switchData{letter}"]["portOut"]["vlan"]
    replacements[f"NAMEIF{letter}IN"] = data[f"switchData{letter}"]["portIn"]["ifName"]
    replacements[f"NAMEIF{letter}OUT"] = data[f"switchData{letter}"]["portOut"]["ifName"]
    replacements[f"SWITCH{letter}OUTGOING"] = data[f"switchData{letter}"]["portOut"]["ifName"]
    replacements[f"SWITCH{letter}INCOMING"] = data[f"switchData{letter}"]["portIn"]["ifName"]
    # replacements[f"SWITCH{letter}IF"] = data[f"switchData{letter}"]["switchif"]
    replacements[f"SNMP{letter}HOSTIP"] = data[f"switchData{letter}"]["SNMPHostIP"]
    # replacements[f"MONITORVLAN{str(i+1)}"] = vlan_if_index[i]
    # replacements[f"MONITORVLAN{str(i+switch_num)}"] = vlan_if_index[i+switch_num]

# replacing
cloud_functions.replacing_json(f"./templates/newTemplate{switch_num}.json","out.json",data,replacements)
cloud_functions.replacing_json(f"./templates/debugTemplate{switch_num}.json","outDebug.json",data,replacements)

# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py out.json outDebug.json {file_name}"
subprocess.run(cmd, shell=True)
