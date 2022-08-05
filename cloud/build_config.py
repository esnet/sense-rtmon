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
config_path = str(os.path.abspath(os.curdir))
infpth = config_path + "/config_template.yml"
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

data['configFile'] = "cloud_config.yml"
data['flow'] = input("Please enter a flow ID: ")
data['hostIP'] = input("Enter ip of this host: ")
data['grafanaHostIP'] =  input("Grafana Host DNS (e.g. dev2.virnao.com): ")
data['grafanaAPIToken'] =  input("Grafana APIToken (Visit Google Doc for Grafana API Key instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub): \n")

print("Host 1: ")
data['hostA']['IP'] = input("Host 1 IP (198.32.43.16): ")
data['hostA']['vlan'] = input("Host 1 VLAN: ")
data['hostA']['switchPort']['ifName'] = input("switch port interface name: ")
data['hostA']['switchPort']['ifVlan'] = f"Vlan {str(data['hostA']['vlan'])}"

print("Host 2: ")
data['hostB']['IP'] = input("Host 2 IP (198.32.43.15): ")
data['hostB']['vlan'] = input("Host 2 VLAN: ")
data['hostB']['switchPort']['ifName'] = input("switch port interface name: ")
data['hostB']['switchPort']['ifVlan'] = f"Vlan {str(data['hostB']['vlan'])}"

print("config switch information:")
data['switchData']['SNMPHostIP'] = input("IP address where SNMP Exporter is running on: ")
data['switchData']['target'] = input("Switch IP: ")
data['switchData']['portIn']['ifName'] = input("PortIn interface name: ")
data['switchData']['portIn']['vlan'] = input("PortIn VLAN: ")
data['switchData']['portIn']['ifVlan'] = f"Vlan {str(data['portIn']['vlan'])}"

data['switchData']['portOut']['ifName'] = input("PortOut interface name: ")
data['switchData']['portOut']['vlan'] = input("PortOut VLAN: ")
data['switchData']['portOut']['ifVlan'] = f"Vlan {str(data['portOut']['vlan'])}"

print("\n Yaml Dumping to cloud_config.yml\n")
with open('../cloud_config.yml', 'w') as outfile:
    yaml.dump(data, outfile, default_flow_style=False)