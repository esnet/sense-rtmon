# erase all urls from this host (instance)
import json
import os
import requests
import yaml
import sys

# get this host's IP address
owd = os.getcwd()
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config_site"
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
            print(f"\n Config file {file_path} could not be found in the config directory\n")
else: # default config file
    with open(infpth, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {infpth} could not be found in the config directory\n")

hostip = data['hostIP']
node_url = f"http://dev2.virnao.com:9091/metrics/job/node-exporter/instance/{hostip}"
requests.delete(node_url)

if data['switchNum'] == 1:
    target = data['snmpMetrics']['target']
    snmp_url = f"http://dev2.virnao.com:9091/metrics/job/snmp-exporter/instance/{hostip}/target_switch/{target}"
    requests.delete(snmp_url)
elif data['switchNum'] == 2:
    target1 = data['snmpMetricsA']['target']
    target2 = data['snmpMetricsB']['target']
    snmp_url = f"http://dev2.virnao.com:9091/metrics/job/snmp-exporter/instance/{hostip}/target_switch/{target1}"
    requests.delete(snmp_url)
    snmp_url = f"http://dev2.virnao.com:9091/metrics/job/snmp-exporter2/instance/{hostip}/target_switch/{target2}"
    requests.delete(snmp_url)

# delete ARP metrics
dir = str(os.getcwd())    
# delete previous urls
delete_file_path = dir + "/Metrics/ARPMetrics/jsonFiles/delete.json"
with open(delete_file_path,"rt") as fp:
# check if the file is empty
    if os.stat(delete_file_path).st_size != 0:
        load_delete = json.load(fp)
        for each_url in load_delete:
            requests.delete(each_url)
            
print("Later added SNMP Exporters need to be deleted manually.")