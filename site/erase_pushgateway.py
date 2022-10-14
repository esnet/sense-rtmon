# erase all urls from this host (instance)
import json
import os
import requests
import yaml
import sys
import site_functions

# read yml file
data,file_name = site_functions.read_yml_file("config_site",sys.argv,1,1)

hostip = data['hostIP']
node_url = f"http://dev2.virnao.com:9091/metrics/job/node-exporter/instance/{hostip}"
requests.delete(node_url)

target = data['snmpMetricsA']['target']
snmp_url = f"http://dev2.virnao.com:9091/metrics/job/snmp-exporter/instance/{hostip}/target_switch/{target}"
requests.delete(snmp_url)
if data['switchNum'] == 2:
    target2 = data['snmpMetricsB']['target']
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