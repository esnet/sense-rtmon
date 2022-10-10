#!/usr/bin/env python3
import re
import yaml
import sys
import subprocess
import os
from datetime import datetime

print("\n\nParsing config file...")
# Load yaml config file as dict
owd = os.getcwd()
os.chdir("..")
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config_flow"
os.chdir(owd)
data = {}

# argument given
file_name = str(sys.argv[1])
file_path = config_path + "/" + file_name
print(f"\n Config file {file_path}\n")
with open(file_path, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(f"\n Config file {file_path} could not be found in the config directory\n")

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

# def index_finder(name):
#     cmd = f"curl {pushgateway_metrics} | tac | grep '.*ifName.*ifName=\"{name}\".*'"
#     grep = subprocess.check_output(cmd,shell=True).decode()
#     if_index = re.search('ifIndex="(.+?)\"',grep).group(1)
#     return if_index

# if_index1 = index_finder(str(data['hostA']['switchPort']['ifName']))
# if_index2 = index_finder(str(data['hostB']['switchPort']['ifName']))

# # monitor per vlan. If same, avoid duplicates monitoring
# if data['switchNum'] == 1: # 1 switch possibly 1 vlan
#     vlan_if_index1 = index_finder(str(data['switchData']['portIn']['ifVlan']))
#     vlan_if_index2 = index_finder(str(data['switchData']['portOut']['ifVlan']))

# # 2 switches possibly 4 vlans
# if data['switchNum'] == 2 or data['switchNum'] == 3:
#     vlan_if_index3 = index_finder(str(data['switchDataA']['portIn']['ifVlan']))
#     vlan_if_index4 = index_finder(str(data['switchDataA']['portOut']['ifVlan']))
#     vlan_if_index5 = index_finder(str(data['switchDataB']['portIn']['ifVlan']))
#     vlan_if_index6 = index_finder(str(data['switchDataB']['portOut']['ifVlan']))
    
######################## COMMENTING FOR TESTING ########################

current_time = datetime.now().strftime("%m/%d_%H:%M")
timeTxt = " | [" + str(current_time) + "]"
if data['switchNum'] == 1:
    print("Single Network Element Flow Detected")
    title1 = f" {str(data['flow'])} | {str(data['hostA']['interfaceName'])}/{str(data['hostA']['vlan'])}--{str(data['switchData']['portIn']['ifName'])}/{str(data['switchData']['portIn']['ifVlan'])}--{str(data['switchData']['portOut']['ifName'])}/{str(data['switchData']['portOut']['ifVlan'])}--{str(data['hostB']['interfaceName'])}/{str(data['hostB']['vlan'])} {timeTxt}"
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
        'IPSWITCH': str(data['switchData']['target']),
        'SNMPNAME': str(data['switchData']['job_name']),
        'SWITCHIF': str(data['switchData']['switchif']),
        'SNMPHOSTIP': str(data['switchData']['SNMPHostIP']),
        'SWITCHAINCOMING': str(data['switchData']['portIn']['ifName']),
        'SWITCHAOUTGOING': str(data['switchData']['portOut']['ifName']),
        'SWITCHAINVLAN': str(data['switchData']['portIn']['vlan']),
        'SWITCHAOUTVLAN': str(data['switchData']['portOut']['vlan']),
        'DASHTITLE':dash_title1,
        'DEBUGTITLE': debug_title1}

if data['switchNum'] == 2:
    print("Two Network Element Flow Detected")
    title2 = f" {str(data['dashTitle'])} {str(data['flow'])} | {str(data['hostA']['interfaceName'])}\{str(data['hostA']['vlan'])}--{str(data['switchDataA']['portIn']['ifName'])}\{str(data['switchDataA']['portIn']['ifVlan'])}--{str(data['switchDataA']['portOut']['ifName'])}\{str(data['switchDataA']['portOut']['ifVlan'])}--{str(data['switchDataB']['portIn']['ifName'])}\{str(data['switchDataB']['portIn']['ifVlan'])}--{str(data['switchDataB']['portOut']['ifName'])}\{str(data['switchDataB']['portOut']['ifVlan'])}--{str(data['hostB']['interfaceName'])}\{str(data['hostB']['vlan'])} {timeTxt}"
    dash_title2 = str(data['dashTitle']) + title2
    debug_title2 = str(data['debugTitle']) + title2
    replacements = {
        'IPHOSTA': str(data['hostA']['IP']), 
        'IPHOSTB': str(data['hostB']['IP']),
        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
        'SNMPHOSTIP': str(data['switchDataA']['SNMPHostIP']),
        'SNMP2HOSTIP': str(data['switchDataB']['SNMPHostIP']),
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
        'SNMPNAME': str(data['switchDataA']['job_name']),
        'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
        'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
        'SWITCHBINVLAN': str(data['switchDataB']['portIn']['vlan']),
        'SWITCHBOUTVLAN': str(data['switchDataB']['portOut']['vlan']),
        'DASHTITLE': dash_title2,
        'DEBUGTITLE': debug_title2}
    replacements = {'MONITORVLAN1': str(vlan_if_index3),
        'MONITORVLAN2': str(vlan_if_index4),
        'MONITORVLAN3': str(vlan_if_index5),
        'MONITORVLAN4': str(vlan_if_index6)
        }
    
if data['switchNum'] == 3:
    print("Three Network Element Flow Detected")
    replacements = {
        'IPHOSTA': str(data['hostA']['IP']), 
        'IPHOSTB': str(data['hostB']['IP']),
        'VLANA': str(data['hostA']['vlan']),
        'VLANB': str(data['hostB']['vlan']),
        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
        'SNMPHOSTIP': str(data['switchDataA']['SNMPHostIP']),
        'SNMP2HOSTIP': str(data['switchDataB']['SNMPHostIP']),
        'SNMP3HOSTIP': str(data['switchDataC']['SNMPHostIP']),
        'IFINDEXSWITCHHOSTA': str(if_index1),
        'MONITORVLAN1': str(vlan_if_index3),
        'MONITORVLAN2': str(vlan_if_index4),
        'MONITORVLAN3': str(vlan_if_index5),
        'MONITORVLAN4': str(vlan_if_index6),
        'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifName']),
        'SWITCHAINCOMING': str(data['switchDataA']['portIN']['ifName']),
        'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifName']),
        'SWITCHBOUTGOING': str(data['switchDataB']['portOut']['ifName']),
        'SWITCHCINCOMING': str(data['switchDataC']['portIn']['ifName']),
        'SWITCHCOUTGOING': str(data['switchDataC']['portOut']['ifName']),
        'IFINDEXSWITCHHOSTB': str(if_index2),
        'NAMEIFAIN': str(data['switchDataA']['portIn']['ifName']),
        'NAMEIFAOUT': str(data['switchDataA']['portOut']['ifName']),
        'NAMEIFBIN': str(data['switchDataB']['portIn']['ifName']),
        'NAMEIFBOUT': str(data['switchDataB']['portOut']['ifName']),
        'NAMEIFCIN': str(data['switchDataC']['portIn']['ifName']),
        'NAMEIFCOUT': str(data['switchDataC']['portOut']['ifName']),
        'DATAPLANEIPA': str(data['hostA']['interfaceIP']),
        'DATAPLANEIPB': str(data['hostB']['interfaceIP']),
        'NODENAMEA': str(data['hostA']['nodeName']),
        'NODENAMEB': str(data['hostB']['nodeName']),
        'IPSWITCHA': str(data['switchDataA']['target']), 
        'IPSWITCHB': str(data['switchDataB']['target']),
        'IPSWITCHC': str(data['switchDataC']['target']),
        'SNMPNAME': str(data['switchDataA']['job_name']),
        'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
        'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
        'SWITCHBINVLAN': str(data['switchDataB']['portIn']['vlan']),
        'SWITCHBOUTVLAN': str(data['switchDataB']['portOut']['vlan']),
        'SWITCHCINVLAN': str(data['switchDataC']['portIn']['vlan']),
        'SWITCHCOUTVLAN': str(data['switchDataC']['portOut']['vlan']),
        'DASHTITLE': f" {str(data['dashTitle'])} 3 switches {timeTxt}",
        'DEBUGTITLE': f" {str(data['debugTitle'])} 3 swtiches {timeTxt}"}

if data['switchNum'] == 4:
    print("Four Network Element Flow Detected")
    replacements = {
        'IPHOSTA': str(data['hostA']['IP']), 
        'IPHOSTB': str(data['hostB']['IP']),
        'VLANA': str(data['hostA']['vlan']),
        'VLANB': str(data['hostB']['vlan']),
        'MONITORVLAN1': str(vlan_if_index1),
        'MONITORVLAN2': str(vlan_if_index2),
        'MONITORVLAN3': str(vlan_if_index3),
        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
        'SNMPHOSTIP': str(data['switchDataA']['SNMPHostIP']),
        'SNMP2HOSTIP': str(data['switchDataB']['SNMPHostIP']),
        'SNMP3HOSTIP': str(data['switchDataC']['SNMPHostIP']),
        'SNMP4HOSTIP': str(data['switchDataD']['SNMPHostIP']),
        'IFINDEXSWITCHHOSTA': str(if_index1),
        'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifName']),
        'SWITCHAINCOMING': str(data['switchDataA']['portIn']['ifName']),
        'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifName']),
        'SWITCHBOUTGOING': str(data['switchDataB']['portOut']['ifName']),
        'SWITCHCINCOMING': str(data['switchDataC']['portIn']['ifName']),
        'SWITCHCOUTGOING': str(data['switchDataC']['portOut']['ifName']),
        'SWITCHDINCOMING': str(data['switchDataD']['portIn']['ifName']),
        'SWITCHDOUTGOING': str(data['switchDataD']['portOut']['ifName']),
        'IFINDEXSWITCHHOSTB': str(if_index2),
        'NAMEIFAIN': str(data['switchDataA']['portIn']['ifName']),
        'NAMEIFAOUT': str(data['switchDataA']['portOut']['ifName']),
        'NAMEIFBIN': str(data['switchDataB']['portIn']['ifName']),
        'NAMEIFBOUT': str(data['switchDataB']['portOut']['ifName']),
        'NAMEIFCIN': str(data['switchDataC']['portIn']['ifName']),
        'NAMEIFCOUT': str(data['switchDataC']['portOut']['ifName']),
        'NAMEIFDIN': str(data['switchDataD']['portIn']['ifName']),
        'NAMEIFDOUT': str(data['switchDataD']['portOut']['ifName']),
        'DATAPLANEIPA': str(data['hostA']['interfaceIP']),
        'DATAPLANEIPB': str(data['hostB']['interfaceIP']),
        'NODENAMEA': str(data['hostA']['nodeName']),
        'NODENAMEB': str(data['hostB']['nodeName']),
        'IPSWITCHA': str(data['switchDataA']['target']),
        'IPSWITCHB': str(data['switchDataB']['target']),
        'IPSWITCHC': str(data['switchDataC']['target']),
        'IPSWITCHD': str(data['switchDataD']['target']),
        'SNMPNAME': str(data['switchDataA']['job_name']),
        'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
        'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
        'SWITCHBINVLAN': str(data['switchDataB']['portIn']['vlan']),
        'SWITCHBOUTVLAN': str(data['switchDataB']['portOut']['vlan']),
        'SWITCHCINVLAN': str(data['switchDataC']['portIn']['vlan']),
        'SWITCHCOUTVLAN': str(data['switchDataC']['portOut']['vlan']),
        'SWITCHDINVLAN': str(data['switchDataD']['portIn']['vlan']),
        'SWITCHDOUTVLAN': str(data['switchDataD']['portOut']['vlan']),
        'DASHTITLE': f" {str(data['dashTitle'])} 4 switches {timeTxt}",
        'DEBUGTITLE': f" {str(data['debugTitle'])} 4 switches {timeTxt}"}

# replacing
with open(f"./templates/newTemplate{str(data['switchNum'])}.json") as infile, open('out.json', 'w') as outfile:
    for line in infile:
        for src, target in replacements.items():
            line = line.replace(src, target)
        outfile.write(line)
with open(f"./templates/debugTemplate{str(data['switchNum'])}.json") as infile, open('outDebug.json', 'w') as outfile:
    for line in infile:
        for src, target in replacements.items():
            line = line.replace(src, target)
        outfile.write(line)              

# Run the API script to convert output JSON to Grafana dashboard automatically
cmd = f"sudo python3 api.py out.json outDebug.json {file_name}"
subprocess.run(cmd, shell=True)
print("\n\n!!   If you do not see: {'id':#, 'slug': <title>, 'status': 'success', 'uid':<>, 'url':<title>, 'version': 1}")