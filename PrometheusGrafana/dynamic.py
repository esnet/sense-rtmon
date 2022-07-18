#!/usr/bin/env python3

import yaml
import sys
import subprocess
import os
from datetime import datetime

print("Parsing config file...")
# Load yaml config file as dict
owd = os.getcwd()
os.chdir("..")
config_path = str(os.path.abspath(os.curdir))
infpth = config_path + "/config.yml"
os.chdir(owd)
data = {}

# argument given
if len(sys.argv) > 1:
    file_name = str(sys.argv[1])
    file_path = config_path + file_name
    with open(file_path, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {file_path} could not be found in the DynamicDashboard directory\n")
else: # default config file
    with open(infpth, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {infpth} could not be found in the DynamicDashboard directory\n")

print("Starting script...")
now = datetime.now()
current_time = now.strftime("%d/%m/%Y_%H:%M")
timeTxt = " ( " + str(current_time) + " )"
# timeTxt = ""
if data['switchNum'] == 1:
    print("Single Network Element Flow Detected")
    print("Collecting dashboard template...")
    # Map of replacements to complete from template.json to out.json
    replacements = {'IPHOSTA': str(data['hostA']['IP']), 
                    'IPHOSTB': str(data['hostB']['IP']),
                    'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
                    'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
                    'IFNAMESWITCHHOSTA': str(data['hostA']['switchPort']['ifIndex']),
                    'NAMEIFSWITCHA': str(data['hostA']['switchPort']['ifName']),
                    'NAMEIFSWITCHB': str(data['hostB']['switchPort']['ifName']),
                    'IFNAMESWITCHHOSTB': str(data['hostB']['switchPort']['ifIndex']),
                    'DATAPLANEIPA': str(data['hostA']['interfaceIP']),
                    'DATAPLANEIPB': str(data['hostB']['interfaceIP']),
                    'NODENAMEA': str(data['hostA']['nodeName']),
                    'NODENAMEB': str(data['hostB']['nodeName']),
                    'VLANA': str(data['hostA']['vlan']),
                    'VLANB': str(data['hostB']['vlan']),
                    'PORTA': str(data['hostA']['nodeExporterPort']),
                    'PORTB': str(data['hostB']['nodeExporterPort']),
                    'ARPPORT': str(data['arpMetrics']['port']),
                    'TCPPORT': str(data['tcpMetrics']['port']),
                    'ARPNAME': str(data['arpMetrics']['job_name']),
                    'TCPNAME': str(data['tcpMetrics']['job_name']),
                    'IPSWITCH': str(data['switchData']['target']),
                    'SNMPNAME': str(data['switchData']['job_name']),
                    'SCRAPEINTERVAL': str(data['switchData']['scrapeInterval']),
                    'PARAMS': str(data['switchData']['params']),
                    'SWITCHIF': str(data['switchData']['switchif']),
                    'SNMPHOSTIP': str(data['switchData']['SNMPHostIP']),
                    'DASHTITLE': str(data['dashTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt,
                    'DEBUGTITLE': str(data['debugTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt}
    print("Creating custom Grafana JSON Dashboard...")
    print("Creating custom L2 Debugging Dashboard...")
    # Iteratively find and replace in one go 
    with open('newTemplate.json') as infile, open('out.json', 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)
    with open('debugTemplate.json') as infile, open('outDebug.json', 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)

    print("Applying dashboard JSON to Grafana API...")
    # Run the API script to convert output JSON to Grafana dashboard automatically
    print("Loading Grafana dashboard on Grafana server...")
    cmd = "sudo python3 api.py out.json outDebug.json"
    subprocess.run(cmd, shell=True)
    print("Loaded Grafana dashboard")
else:
    print("Multiple Network Element Flow Detected")
    print("Collecting dashboard template...")
    # Map of replacements to complete from template.json to out.json
    replacements = {}
    if data['switchNum'] == 2:
        replacements = {'IPHOSTA': str(data['hostA']['IP']), 
                        'IPHOSTB': str(data['hostB']['IP']),
                        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
                        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
                        'IFNAMESWITCHHOSTA': str(data['hostA']['switchPort']['ifIndex']),
                        'IFNAMESWITCHHOSTB': str(data['hostB']['switchPort']['ifIndex']),
                        'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifIndex']),
                        'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifIndex']),
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
                        'PORTA': str(data['hostA']['nodeExporterPort']),
                        'PORTB': str(data['hostB']['nodeExporterPort']),
                        'ARPPORT': str(data['arpMetrics']['port']),
                        'TCPPORT': str(data['tcpMetrics']['port']),
                        'ARPNAME': str(data['arpMetrics']['job_name']),
                        'TCPNAME': str(data['tcpMetrics']['job_name']),
                        'IPSWITCHA': str(data['switchDataA']['target']),
                        'IPSWITCHB': str(data['switchDataB']['target']),
                        'SWITCHIF': str(data['switchData']['switchif']),
                        'SNMPNAME': str(data['switchDataA']['job_name']),
                        'DASHTITLE': str(data['dashTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt,
                        'DEBUGTITLE': str(data['debugTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt}
    elif data['switchNum'] == 3:
        replacements = {'IPHOSTA': str(data['hostA']['IP']), 
                        'IPHOSTB': str(data['hostB']['IP']),
                        'VLANA': str(data['hostA']['vlan']),
                        'VLANB': str(data['hostB']['vlan']),
                        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
                        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
                        'IFNAMESWITCHHOSTA': str(data['hostA']['switchPort']['ifIndex']),
                        'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifIndex']),
                        'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifIndex']),
                        'SWITCHBOUTGOING': str(data['switchDataB']['portOut']['ifIndex']),
                        'SWITCHCINCOMING': str(data['switchDataC']['portIn']['ifIndex']),
                        'IFNAMESWITCHHOSTB': str(data['hostB']['switchPort']['ifIndex']),
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
                        'PORTA': str(data['hostA']['nodeExporterPort']),
                        'PORTB': str(data['hostB']['nodeExporterPort']),
                        'ARPPORT': str(data['arpMetrics']['port']),
                        'TCPPORT': str(data['tcpMetrics']['port']),
                        'ARPNAME': str(data['arpMetrics']['job_name']),
                        'TCPNAME': str(data['tcpMetrics']['job_name']),
                        'IPSWITCHA': str(data['switchDataA']['target']), 
                        'IPSWITCHB': str(data['switchDataB']['target']),
                        'IPSWITCHC': str(data['switchDataC']['target']),
                        'SWITCHIF': str(data['switchData']['switchif']),
                        'SNMPNAME': str(data['switchDataA']['job_name']),
                        'DASHTITLE': str(data['dashTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt,
                        'DEBUGTITLE': str(data['debugTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt}
    else:
        replacements = {'IPHOSTA': str(data['hostA']['IP']), 
                        'IPHOSTB': str(data['hostB']['IP']),
                        'VLANA': str(data['hostA']['vlan']),
                        'VLANB': str(data['hostB']['vlan']),
                        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
                        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
                        'IFNAMESWITCHHOSTA': str(data['hostA']['switchPort']['ifIndex']),
                        'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifIndex']),
                        'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifIndex']),
                        'SWITCHBOUTGOING': str(data['switchDataB']['portOut']['ifIndex']),
                        'SWITCHCINCOMING': str(data['switchDataC']['portIn']['ifIndex']),
                        'SWITCHCOUTGOING': str(data['switchDataC']['portOut']['ifIndex']),
                        'SWITCHDINCOMING': str(data['switchDataD']['portIn']['ifIndex']),
                        'IFNAMESWITCHHOSTB': str(data['hostB']['switchPort']['ifIndex']),
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
                        'PORTA': str(data['hostA']['nodeExporterPort']),
                        'PORTB': str(data['hostB']['nodeExporterPort']),
                        'ARPPORT': str(data['arpMetrics']['port']),
                        'TCPPORT': str(data['tcpMetrics']['port']),
                        'ARPNAME': str(data['arpMetrics']['job_name']),
                        'TCPNAME': str(data['tcpMetrics']['job_name']),
                        'IPSWITCHA': str(data['switchDataA']['target']),
                        'IPSWITCHB': str(data['switchDataB']['target']),
                        'IPSWITCHC': str(data['switchDataC']['target']),
                        'IPSWITCHD': str(data['switchDataD']['target']),
                        'SWITCHIF': str(data['switchData']['switchif']),
                        'SNMPNAME': str(data['switchDataA']['job_name']),
                        'DASHTITLE': str(data['dashTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt,
                        'DEBUGTITLE': str(data['debugTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt}
    print("Creating custom Grafana JSON Dashboard...")
    print("Creating custom L2 Debugging JSON Dashboard...")
    # Iteratively find and replace in one go 
    fname = "template" + str(data['switchNum']) + ".json"
    dname = "debugTemplate" + str(data['switchNum']) + ".json"
    with open(fname) as infile, open('out.json', 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)
    with open(dname) as infile, open('outDebug.json', 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)              
    print("Applying dashboard JSON to Grafana API...")
    # Run the API script to convert output JSON to Grafana dashboard automatically
    print("Loading Grafana dashboard on Grafana server...")
    cmd = "sudo python3 api.py out.json outDebug.json"
    subprocess.run(cmd, shell=True)
    print("Loaded Grafana dashboard")
