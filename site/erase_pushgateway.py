# erase all urls from this host (instance)
import json
import os
import requests
import yaml

# get this host's IP address
owd = os.getcwd()
os.chdir("..")
infpth = str(os.path.abspath(os.curdir)) + "/config.yml"
os.chdir(owd)
data = {}
with open(infpth, 'r') as stream:
    data = yaml.safe_load(stream)

hostip = data['hostIP']

dir = str(os.getcwd())    
# delete previous urls
delete_file_path = dir + "/../Metrics/ARPMetrics/jsonFiles/delete.json"
with open(delete_file_path,"rt") as fp:
# check if the file is empty
    if os.stat(delete_file_path).st_size != 0:
        load_delete = json.load(fp)
        for each_url in load_delete:
            requests.delete(each_url)

node_url = f"http://dev2.virnao.com:9091/metrics/job/node-exporter/instance/{hostip}"
snmp_url = f"http://dev2.virnao.com:9091/metrics/job/snmp-exporter/instance/{hostip}"
requests.delete(node_url)
requests.delete(snmp_url)
