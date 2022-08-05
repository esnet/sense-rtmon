# erase all urls from this host (instance)
import json
import os
import requests
import yaml
import sys

# get this host's IP address
owd = os.getcwd()
os.chdir("..")
infpth = str(os.path.abspath(os.curdir)) + "/config.yml"
config_path = str(os.path.abspath(os.curdir))
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

# delete ARP metrics
dir = str(os.getcwd())    
# delete previous urls
delete_file_path = dir + "/../Metrics/ARPMetrics/jsonFiles/delete.json"
with open(delete_file_path,"rt") as fp:
# check if the file is empty
    if os.stat(delete_file_path).st_size != 0:
        load_delete = json.load(fp)
        for each_url in load_delete:
            requests.delete(each_url)

hostip = data['hostIP']
node_url = f"http://dev2.virnao.com:9091/metrics/job/node-exporter/instance/{hostip}"
requests.delete(node_url)
            
if data['switchNum'] == 1:
    target = data['switchData']['target']
    vlan_to_switch = data['vlan_to_switch']
    snmp_url = f"http://dev2.virnao.com:9091/metrics/job/snmp-exporter/instance/{hostip}/target_switch/{target}"
    requests.delete(snmp_url)
elif data['switchNum'] == 2:
    target1 = data['switchDataA']['target']
    target2 = data['switchDataB']['target']
    vlan1 = data['hostA']['vlan']
    vlan2 = data['hostB']['vlan']    
    snmp_url = f"http://dev2.virnao.com:9091/metrics/job/snmp-exporter/instance/{hostip}/target_switch/{target1}"
    requests.delete(snmp_url)

