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

# if_index1 = cloud_functions.index_finder(pushgateway_metrics,str(data["hostA"]["switchPort"]["ifName"]))
# if_index2 = cloud_functions.index_finder(pushgateway_metrics,str(data["hostB"]["switchPort"]["ifName"]))

vlan_if_index=[]
for i in range(int(data["switchNum"])*2):
    letter = chr(ord('A')+i) # A B C D ... 
    vlan_if_index.append(f"MONITORVLAN{i}")
#     vlan_if_index.append(cloud_functions.index_finder(pushgateway_metrics,str(data[f"switchData{letter}"]["portIn"]["ifVlan"])))
#     vlan_if_index.append(cloud_functions.index_finder(pushgateway_metrics,str(data[f"switchData{letter}"]["portOut"]["ifVlan"])))
    
# # monitor per vlan. If same, avoid duplicates monitoring
# 1 switch possibly 1 vlan
# vlan_if_index1 = index_finder(str(data["switchDataA"]["portIn"]["ifVlan"]))
# vlan_if_index2 = index_finder(str(data["switchDataA"]["portOut"]["ifVlan"]))

# # 2 switches possibly 4 vlans
# if switch_num > 1:
#     vlan_if_index3 = index_finder(str(data["switchDataB"]["portIn"]["ifVlan"]))
#     vlan_if_index4 = index_finder(str(data["switchDataB"]["portOut"]["ifVlan"]))

# if switch_num > 2: # 3 switches possibly 6 vlans
#     vlan_if_index5 = index_finder(str(data["switchDataC"]["portIn"]["ifVlan"]))
#     vlan_if_index6 = index_finder(str(data["switchDataC"]["portOut"]["ifVlan"]))
    

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
replacements["IFINDEXSWITCHHOSTA"] = if_index1
replacements["IFINDEXSWITCHHOSTB"] = if_index2
replacements["DATAPLANEIPA"] = data["hostA"]["interfaceIP"]
replacements["DATAPLANEIPB"] = data["hostB"]["interfaceIP"]
replacements["NODENAMEA"] = data["hostA"]["nodeName"]
replacements["NODENAMEB"] = data["hostB"]["nodeName"]
replacements["NAMEIFSWITCHA"] = data["hostA"]["switchPort"]["ifName"]
replacements["NAMEIFSWITCHB"] = data["hostB"]["switchPort"]["ifName"]
    
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
    replacements[f"SWITCH{letter}IF"] = data[f"switchData{letter}"]["switchif"]
    replacements[f"SNMP{letter}HOSTIP"] = data[f"switchData{letter}"]["SNMPHostIP"]
    replacements[f"MONITORVLAN{str(i+1)}"] = vlan_if_index[i]
    replacements[f"MONITORVLAN{str(i+switch_num)}"] = vlan_if_index[i+switch_num]
 
# replacing
cloud_functions.replacing_json(f'./templates/newTemplate{switch_num}.json',"out.json",data,replacements)
cloud_functions.replacing_json(f'./templates/debugTemplate{switch_num}.json',"outDebug.json",data,replacements)

# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py out.json outDebug.json {file_name}"
subprocess.run(cmd, shell=True)
print("\n\n!!   If you do not see: {'id':#, 'slug': <title>, 'status': 'success', 'uid':<>, 'url':<title>, 'version': 1}")