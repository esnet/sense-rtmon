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

data['flow'] = "abc"
with open('cloud_generated_config.yml', 'w') as outfile:
    yaml.dump(data, outfile, default_flow_style=False)
    
# # Flow number
# flow: " flow 2 "
# # This host's IP address
# hostIP: 198.32.43.16
# grafanaHostIP: 'dev2.virnao.com'
# grafanaAPIToken: "Bearer eyJrIjoiNWYwWEFzVTRUUHQ5TWg3cVBUdHpMV01PREo1aWJmeUkiLCJuIjoiMDcvMTQiLCJpZCI6MX0="
# configFile: "config.yml"

# # Host 1 Specifics 
# hostA:
#   IP: 198.32.43.16
#   interfaceName: 'ens2f0np0.1000'
#   interfaceIP: '10.10.100.1'
#   nodeName: 'sdn-dtn-2-10.ultralight.org'
#   vlan: 1000
#   nodeExporterPort: 9100
#   switchPort: 
#     ifName: 'hundredGigE 1/27'
#     ifVlan: 'Vlan 1000'

# # Host 2 Specifics
# hostB:
#   IP: 198.32.43.15
#   interfaceName: 'ens2f0.1000'
#   interfaceIP: '10.10.100.2'
#   nodeName: 'sdn-dtn-2-11.ultralight.org'
#   vlan: 1000
#   nodeExporterPort: 9100
#   switchPort: 
#     ifName: 'hundredGigE 1/31'
#     ifVlan: 'Vlan 1000'

# switchData:
#   job_name: 'snmp1'
#   # The IP of the host which is running the SNMP Exporter container
#   SNMPHostIP: 198.32.43.16
#   # Scrape interval/duration time
#   scrapeInterval: 15s
#   scrapeDuration: 5h
#   target: 172.16.1.1
#   # switch if format: " - IF: optional"
#   switchif: ""
#   #if-mib and F10-IF-EXTENSION-MIB
#   params: ['if_mib']
#   portIn: 
#     ifName: 'hundredGigE 1/27'
#     vlan: 1000
#     vlanName: 'Vlan 1000'
#   portOut: 
#     ifName: 'hundredGigE 1/31'
#     vlan: 1000
#     vlanName: 'Vlan 1000'

