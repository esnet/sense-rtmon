#!/usr/bin/env python3
import re
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
    file_path = config_path + "/" + file_name
    print(f"\n Config file {file_path}\n")
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

print("find correct index from snmp exporter")
# find correct inter face index from SNMP exporter
myip = data['hostIP']
pushgateway_metrics = f"{myip}:9091/metrics"

cmd1 = f"curl {pushgateway_metrics} | grep '.*ifName.*ifDescr=\"{str(data['hostA']['switchPort']['ifName'])}\".*ifName=\"{str(data['hostA']['switchPort']['ifName'])}\".*'"
subprocess.run(cmd1,shell=True)
subprocess.run("echo \"trial run\"",shell=True)
grep1 = subprocess.check_output(cmd1,shell=True).decode()
subprocess.run("echo \"grep 1\"",shell=True) # acts as enter in command line

cmd2 = f"curl {pushgateway_metrics} | grep '.*ifName.*ifDescr=\"{str(data['hostB']['switchPort']['ifName'])}\".*ifName=\"{str(data['hostB']['switchPort']['ifName'])}\".*'"
grep2 = subprocess.check_output(cmd2,shell=True).decode()
subprocess.run("echo \"grep 2\"",shell=True) # acts as enter in command line

if_index1 = re.search('ifIndex="(.+?)\"',grep1).group(1)
if_index2 = re.search('ifIndex="(.+?)\"',grep2).group(1)

print("Starting script...")
now = datetime.now()
current_time = now.strftime("%m/%d_%H:%M")
timeTxt = "   [" + str(current_time) + "]"
# timeTxt = ""
if data['switchNum'] == 1:
    print("Single Network Element Flow Detected")
    print("Collecting dashboard template...")
    # Map of replacements to complete from template.json to out.json
    replacements = {'IPHOSTA': str(data['hostA']['IP']), 
                    'IPHOSTB': str(data['hostB']['IP']),
                    'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
                    'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
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
                    'HOSTA_SNMP_ON': "host1_snmp_on_" + str(data['hostA']['vlan']),
                    'HOSTB_SNMP_ON': "host2_snmp_on_" + str(data['hostB']['vlan']),
                    'SWITCH_HOSTA_MAC': "switch_host1_mac_" + str(data['hostA']['vlan']),
                    'SWITCH_HOSTB_MAC': "switch_host2_mac_" + str(data['hostB']['vlan']),
                    'SWITCHAINCOMING': str(data['switchData']['portIn']['ifName']),
                    'SWITCHAOUTGOING': str(data['switchData']['portOut']['ifName']),
                    'SWITCHAINVLAN': str(data['switchData']['portIn']['vlan']),
                    'SWITCHAOUTVLAN': str(data['switchData']['portOut']['vlan']),
                    # 'DASHTITLE': str(data['dashTitle']) + str(data['flow']) + "vlan " + str(data['vlan_to_switch'])+ " " + timeTxt,
                    'DASHTITLE': f"   {str(data['dashTitle'])} {str(data['flow'])} {str(data['hostA']['interfaceName'])}--{str(data['switchData']['portIn']['ifName'])}--{str(data['switchData']['portOut']['ifName'])}--{str(data['hostB']['interfaceName'])} {timeTxt}",
                    'DEBUGTITLE': f"   {str(data['debugTitle'])} {str(data['flow'])} {str(data['hostA']['interfaceName'])}--{str(data['switchData']['portIn']['ifName'])}--{str(data['switchData']['portOut']['ifName'])}--{str(data['hostB']['interfaceName'])} {timeTxt}"}
    
    print("Creating custom Grafana JSON Dashboard...")
    print("Creating custom L2 Debugging Dashboard...")
    # Iteratively find and replace in one go 
    with open('./templates/newTemplate.json') as infile, open('out.json', 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)
    with open('./templates/debugTemplate.json') as infile, open('outDebug.json', 'w') as outfile:
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
                        'IFINDEXSWITCHHOSTA': str(if_index1),
                        'IFINDEXSWITCHHOSTB': str(if_index2),
                        'SWITCHAINCOMING': str(data['switchDataA']['portIn']['ifName']),
                        'SWITCHBOUTGOING': str(data['switchDataB']['portOut']['ifName']),
                        'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifName']),
                        'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifName']),
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
                        'SNMPNAME': str(data['switchDataA']['job_name']),
                        'HOSTA_SNMP_ON': "m_host1_snmp_on_" + str(data['hostA']['vlan']),
                        'HOSTB_SNMP_ON': "m_host2_snmp_on_" + str(data['hostB']['vlan']),
                        'SWITCH_HOSTA_MAC': "m_switch_host1_mac_" + str(data['hostA']['vlan']),
                        'SWITCH_HOSTB_MAC': "m_switch_host2_mac_" + str(data['hostB']['vlan']),
                        'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
                        'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
                        'SWITCHBINVLAN': str(data['switchDataB']['portIn']['vlan']),
                        'SWITCHBOUTVLAN': str(data['switchDataB']['portOut']['vlan']),
                        'DASHTITLE': f"   {str(data['dashTitle'])} {str(data['flow'])} {str(data['hostA']['interfaceName'])}--{str(data['switchDataA']['portIn']['ifName'])}--{str(data['switchDataA']['portOut']['ifName'])}--{str(data['switchDataB']['portIn']['ifName'])}--{str(data['switchDataB']['portOut']['ifName'])}--{str(data['hostB']['interfaceName'])} {timeTxt}",
                        'DEBUGTITLE': f"   {str(data['debugTitle'])} {str(data['flow'])} {str(data['hostA']['interfaceName'])}--{str(data['switchDataA']['portIn']['ifName'])}--{str(data['switchDataA']['portOut']['ifName'])}--{str(data['switchDataB']['portIn']['ifName'])}--{str(data['switchDataB']['portOut']['ifName'])}--{str(data['hostB']['interfaceName'])} {timeTxt}"}
    elif data['switchNum'] == 3:
        replacements = {'IPHOSTA': str(data['hostA']['IP']), 
                        'IPHOSTB': str(data['hostB']['IP']),
                        'VLANA': str(data['hostA']['vlan']),
                        'VLANB': str(data['hostB']['vlan']),
                        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
                        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
                        'IFINDEXSWITCHHOSTA': str(if_index1),
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
                        'PORTA': str(data['hostA']['nodeExporterPort']),
                        'PORTB': str(data['hostB']['nodeExporterPort']),
                        'ARPPORT': str(data['arpMetrics']['port']),
                        'TCPPORT': str(data['tcpMetrics']['port']),
                        'ARPNAME': str(data['arpMetrics']['job_name']),
                        'TCPNAME': str(data['tcpMetrics']['job_name']),
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
                        'DASHTITLE': f"   {str(data['dashTitle'])} {str(data['flow'])} {str(data['hostA']['interfaceName'])}--{str(data['switchDataA']['portIn']['ifName'])}--{str(data['switchDataA']['portOut']['ifName'])}--{str(data['switchDataB']['portIn']['ifName'])}--{str(data['switchDataB']['portOut']['ifName'])}--{str(data['switchDataC']['portIn']['ifName'])}--{str(data['switchDataC']['portOut']['ifName'])}--{str(data['hostB']['interfaceName'])} {timeTxt}",
                        'DEBUGTITLE': f"   {str(data['debugTitle'])} {str(data['flow'])} {str(data['hostA']['interfaceName'])}--{str(data['switchDataA']['portIn']['ifName'])}--{str(data['switchDataA']['portOut']['ifName'])}--{str(data['switchDataB']['portIn']['ifName'])}--{str(data['switchDataB']['portOut']['ifName'])}--{str(data['switchDataC']['portIn']['ifName'])}--{str(data['switchDataC']['portOut']['ifName'])}--{str(data['hostB']['interfaceName'])} {timeTxt}"}
    else:
        replacements = {'IPHOSTA': str(data['hostA']['IP']), 
                        'IPHOSTB': str(data['hostB']['IP']),
                        'VLANA': str(data['hostA']['vlan']),
                        'VLANB': str(data['hostB']['vlan']),
                        'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
                        'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
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
                        'SNMPNAME': str(data['switchDataA']['job_name']),
                        'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
                        'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
                        'SWITCHBINVLAN': str(data['switchDataB']['portIn']['vlan']),
                        'SWITCHBOUTVLAN': str(data['switchDataB']['portOut']['vlan']),
                        'SWITCHCINVLAN': str(data['switchDataC']['portIn']['vlan']),
                        'SWITCHCOUTVLAN': str(data['switchDataC']['portOut']['vlan']),
                        'SWITCHDINVLAN': str(data['switchDataD']['portIn']['vlan']),
                        'SWITCHDOUTVLAN': str(data['switchDataD']['portOut']['vlan']),
                        'DASHTITLE': f"   {str(data['dashTitle'])} {str(data['flow'])} {str(data['hostA']['interfaceName'])}--{str(data['switchDataA']['portIn']['ifName'])}--{str(data['switchDataA']['portOut']['ifName'])}--{str(data['switchDataB']['portIn']['ifName'])}--{str(data['switchDataB']['portOut']['ifName'])}--{str(data['switchDataC']['portIn']['ifName'])}--{str(data['switchDataC']['portOut']['ifName'])}--{str(data['switchDataD']['portIn']['ifName'])}--{str(data['switchDataD']['portOut']['ifName'])}--{str(data['hostB']['interfaceName'])} {timeTxt}",
                        'DEBUGTITLE': f"   {str(data['debugTitle'])} {str(data['flow'])} {str(data['hostA']['interfaceName'])}--{str(data['switchDataA']['portIn']['ifName'])}--{str(data['switchDataA']['portOut']['ifName'])}--{str(data['switchDataB']['portIn']['ifName'])}--{str(data['switchDataB']['portOut']['ifName'])}--{str(data['switchDataC']['portIn']['ifName'])}--{str(data['switchDataC']['portOut']['ifName'])}--{str(data['switchDataD']['portIn']['ifName'])}--{str(data['switchDataD']['portOut']['ifName'])}--{str(data['hostB']['interfaceName'])} {timeTxt}"}
    # print("Creating custom Grafana JSON Dashboard...")
    # print("Creating custom L2 Debugging JSON Dashboard...")
    # Iteratively find and replace in one go 
    fname = "./templates/template" + str(data['switchNum']) + ".json"
    dname = "./templates/debugTemplate" + str(data['switchNum']) + ".json"
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
    # print("Applying dashboard JSON to Grafana API...")
    # Run the API script to convert output JSON to Grafana dashboard automatically
    # print("Loading Grafana dashboard on Grafana server...")
    cmd = "sudo python3 api.py out.json outDebug.json"
    subprocess.run(cmd, shell=True)
    # print("Loaded Grafana dashboard")

print("\n\nIf you do not see:")
print("{'id':#, 'slug': 'title', 'status': 'success', ...'title', 'version': 1")
print("PLEASE RUN ./start.sh AGAIN")
print("Else the dashboards are generated successfully\n\n")