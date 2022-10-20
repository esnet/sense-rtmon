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

print("find correct index from snmp exporter\n\n")
pushgateway_metrics = f"{data['hostIP']}:9091/metrics"

# # holders for interface index
if_index1 = "IFINDEXSWITCHHOSTA"
if_index2 = "IFINDEXSWITCHHOSTB"

vlan_if_index1 = "MONITORVLAN1"
vlan_if_index2 = "MONITORVLAN2"
vlan_if_index3 = "MONITORVLAN3"
vlan_if_index4 = "MONITORVLAN4"
vlan_if_index5 = "MONITORVLAN5"
vlan_if_index6 = "MONITORVLAN6"

### commenting the below allows dashboard generation but the following are needed for SNMP monitoring ###

######################## COMMENTING FOR TESTING ########################

# if_index1 = cloud_functions.index_finder(pushgateway_metrics,str(data['hostA']['switchPort']['ifName']))
# if_index2 = cloud_functions.index_finder(pushgateway_metrics,str(data['hostB']['switchPort']['ifName']))

# vlan_if_index=[]
# for i in range(int(data["switchNum"])*2):
#     letter = chr(ord('A')+i) # A B C D ... 
#     vlan_if_index.append(cloud_functions.index_finder(pushgateway_metrics,str(data[f"switchData{letter}"]['portIn']['ifVlan'])))
#     vlan_if_index.append(cloud_functions.index_finder(pushgateway_metrics,str(data[f"switchData{letter}"]['portOut']['ifVlan'])))
    
# # monitor per vlan. If same, avoid duplicates monitoring
# 1 switch possibly 1 vlan
# vlan_if_index1 = index_finder(str(data['switchDataA']['portIn']['ifVlan']))
# vlan_if_index2 = index_finder(str(data['switchDataA']['portOut']['ifVlan']))

# # 2 switches possibly 4 vlans
# if data['switchNum'] > 1:
#     vlan_if_index3 = index_finder(str(data['switchDataB']['portIn']['ifVlan']))
#     vlan_if_index4 = index_finder(str(data['switchDataB']['portOut']['ifVlan']))

# if data['switchNum'] > 2: # 3 switches possibly 6 vlans
#     vlan_if_index5 = index_finder(str(data['switchDataC']['portIn']['ifVlan']))
#     vlan_if_index6 = index_finder(str(data['switchDataC']['portOut']['ifVlan']))
    

######################## COMMENTING FOR TESTING ########################

current_time = datetime.now().strftime("%m/%d_%H:%M")
timeTxt = " | [" + str(current_time) + "]"
if data['switchNum'] == 1:
    print("Single Network Element Flow Detected")
    title1 = f" {str(data['flow'])} | {str(data['hostA']['interfaceName'])}/{str(data['hostA']['vlan'])}--{str(data['switchDataA']['portIn']['ifName'])}/{str(data['switchDataA']['portIn']['ifVlan'])}--{str(data['switchDataA']['portOut']['ifName'])}/{str(data['switchDataA']['portOut']['ifVlan'])}--{str(data['hostB']['interfaceName'])}/{str(data['hostB']['vlan'])} {timeTxt}"
    # alternative title naming
    title1 = f" {str(data['flow'])} | {str(data['configFile'])} {timeTxt}"
    dash_title1 = str(data['dashTitle']) + title1
    debug_title1 = str(data['debugTitle']) + title1
    # Map of replacements to complete from template.json to out.json
    replacements = {
        'IPHOSTA': str(data['hostA']['IP']), 
        'IPHOSTB': str(data['hostB']['IP']),
        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
        'MONITORVLAN1': str(vlan_if_index1),
        'MONITORVLAN2': str(vlan_if_index2),
        'IFINDEXSWITCHHOSTA': str(if_index1),
        'NAMEIFSWITCHA': str(data['hostA']['switchPort']['ifName']),
        'NAMEIFSWITCHB': str(data['hostB']['switchPort']['ifName']),
        'IFINDEXSWITCHHOSTB': str(if_index2),
        'DATAPLANEIPA': str(data['hostA']['interfaceIP']),
        'DATAPLANEIPB': str(data['hostB']['interfaceIP']),
        'NODENAMEA': str(data['hostA']['nodeName']),
        'NODENAMEB': str(data['hostB']['nodeName']),
        'VLANA': str(data['hostA']['vlan']),
        'VLANB': str(data['hostB']['vlan']),
        'IPSWITCHA': str(data['switchDataA']['target']),
        'SNMPANAMEA': str(data['switchDataA']['job_name']),
        'SWITCHIFA': str(data['switchDataA']['switchif']),
        'SNMPAHOSTIP': str(data['switchDataA']['SNMPHostIP']),
        'SWITCHAINCOMING': str(data['switchDataA']['portIn']['ifName']),
        'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifName']),
        'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
        'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
        'DASHTITLE':dash_title1,
        'DEBUGTITLE': debug_title1}

if data['switchNum'] == 2:
    print("Two Network Element Flow Detected")
    title2 = f" {str(data['flow'])} | {str(data['hostA']['interfaceName'])}/{str(data['hostA']['vlan'])}--{str(data['switchDataA']['portIn']['ifName'])}/{str(data['switchDataA']['portIn']['ifVlan'])}--{str(data['switchDataA']['portOut']['ifName'])}/{str(data['switchDataA']['portOut']['ifVlan'])}--{str(data['switchDataB']['portIn']['ifName'])}/{str(data['switchDataB']['portIn']['ifVlan'])}--{str(data['switchDataB']['portOut']['ifName'])}/{str(data['switchDataB']['portOut']['ifVlan'])}--{str(data['hostB']['interfaceName'])}/{str(data['hostB']['vlan'])} {timeTxt}"
    # alternative title naming
    title2 = f" {str(data['flow'])} | {str(data['configFile'])} {timeTxt}"
    dash_title2 = str(data['dashTitle']) + title2
    debug_title2 = str(data['debugTitle']) + title2
    replacements = {
        'IPHOSTA': str(data['hostA']['IP']), 
        'IPHOSTB': str(data['hostB']['IP']),
        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
        'SNMPAHOSTIP': str(data['switchDataA']['SNMPHostIP']),
        'SNMPBHOSTIP': str(data['switchDataB']['SNMPHostIP']),
        'MONITORVLAN1': str(vlan_if_index3),
        'MONITORVLAN2': str(vlan_if_index4),
        'MONITORVLAN3': str(vlan_if_index5),
        'MONITORVLAN4': str(vlan_if_index6),
        'IFINDEXSWITCHHOSTA': str(if_index1),
        'IFINDEXSWITCHHOSTB': str(if_index2),
        'SWITCHAINCOMING': str(data['switchDataA']['portIn']['ifName']),
        'SWITCHBOUTGOING': str(data['switchDataB']['portOut']['ifName']),
        'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifName']),
        'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifName']),
        'NAMEIFSWITCHA': str(data['hostA']['switchPort']['ifName']),
        'NAMEIFSWITCHB': str(data['hostB']['switchPort']['ifName']),
        'NAMEIFAIN': str(data['hostA']['switchPort']['ifName']),
        'NAMEIFAOUT': str(data['switchDataA']['portOut']['ifName']),
        'NAMEIFBIN': str(data['switchDataB']['portIn']['ifName']),
        'NAMEIFBOUT': str(data['hostB']['switchPort']['ifName']),
        'DATAPLANEIPA': str(data['hostA']['interfaceIP']),
        'DATAPLANEIPB': str(data['hostB']['interfaceIP']),
        'NODENAMEA': str(data['hostA']['nodeName']),
        'NODENAMEB': str(data['hostB']['nodeName']),
        'VLANA': str(data['hostA']['vlan']),
        'VLANB': str(data['hostB']['vlan']),
        'IPSWITCHA': str(data['switchDataA']['target']),
        'IPSWITCHB': str(data['switchDataB']['target']),
        'SNMPANAME': str(data['switchDataA']['job_name']),
        'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
        'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
        'SWITCHBINVLAN': str(data['switchDataB']['portIn']['vlan']),
        'SWITCHBOUTVLAN': str(data['switchDataB']['portOut']['vlan']),
        'DASHTITLE': dash_title2,
        'DEBUGTITLE': debug_title2}
    
# dash_title = data["dashTitle"] + cloud_functions.make_title(data)
# debug_title = data["debugTitle"] + cloud_functions.make_title(data)
# replacements = cloud_functions.replacement_template()
# replacements["DASHTITLE"] = dash_title
# replacements["DEBUGTITLE"] = debug_title
# replacements["IPHOSTA"] = data["hostA"]["IP"]
# replacements["IPHOSTB"] = data["hostB"]["IP"]
# replacements["VLANA"] = data["hostA"]["vlan"]
# replacements["VLANB"] = data["hostB"]["vlan"]
# replacements["IFNAMEHOSTA"] = data["hostA"]["interfaceName"]
# replacements["IFNAMEHOSTB"] = data["hostB"]["interfaceName"]
# replacements["IFINDEXSWITCHHOSTA"] = if_index1
# replacements["IFINDEXSWITCHHOSTB"] = if_index2
# replacements["DATAPLANEIPA"] = data["hostA"]["interfaceIP"]
# replacements["DATAPLANEIPB"] = data["hostB"]["interfaceIP"]
# replacements["NODENAMEA"] = data["hostA"]["nodeName"]
# replacements["NODENAMEB"] = data["hostB"]["nodeName"]

    
# for i in range(int(data['switchNum'])):
#     letter = chr(ord('A')+i) # A B C D ... 
#     replacements[f"IPSWITCH{letter}"] = data[f"switchData{letter}"]["target"]
#     replacements[f"SNMP{letter}NAME"]= data[f"switchData{letter}"]["job_name"]
#     replacements[f"SWITCH{letter}INVLAN"]= data[f"switchData{letter}"]["portIn"]["vlan"]
#     replacements[f"SWITCH{letter}OUTVLAN"]= data[f"switchData{letter}"]["portOut"]["vlan"]
#     replacements[f"NAMEIF{letter}IN"] = data[f"switchData{letter}"]["portIn"]["ifName"]
#     replacements[f"NAMEIF{letter}OUT"] = data[f"switchData{letter}"]["portOut"]["ifName"]
#     replacements[f"SWITCH{letter}OUTGOING"] = data[f"switchData{letter}"]["portOut"]["ifName"]
#     replacements[f"SWITCH{letter}INCOMING"] = data[f"switchData{letter}"]["portIn"]["ifName"]
#     replacements[f"SNMP{letter}HOSTIP"] = data[f"switchData{letter}"]["SNMPHostIP"]
#     replacements[f"MONITORVLAN{str(i+1)}"] = vlan_if_index[i]
#     replacements[f"MONITORVLAN{str(i+int(data['switchNum']))}"] = vlan_if_index[i+int(data['switchNum'])]
 
# replacing
cloud_functions.replacing_json(f"./templates/newTemplate{str(data['switchNum'])}.json",'out.json',data,replacements)

cloud_functions.replacing_json(f"./templates/debugTemplate{str(data['switchNum'])}.json",'outDebug.json',data,replacements)

# with open(f"./templates/newTemplate{str(data['switchNum'])}.json") as infile, open('out.json', 'w') as outfile:
#     for line in infile:
#         for src, target in replacements.items():
#             line = line.replace(src, target)
#         outfile.write(line)
# with open(f"./templates/debugTemplate{str(data['switchNum'])}.json") as infile, open('outDebug.json', 'w') as outfile:
#     for line in infile:
#         for src, target in replacements.items():
#             line = line.replace(src, target)
#         outfile.write(line)              

# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py out.json outDebug.json {file_name}"
subprocess.run(cmd, shell=True)
print("\n\n!!   If you do not see: {'id':#, 'slug': <title>, 'status': 'success', 'uid':<>, 'url':<title>, 'version': 1}")