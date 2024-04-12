"""Test Debug Prometheus Push"""
import yaml
import sys
import os
import time
import datetime
import copy
import requests
import pprint
import simplejson as json
import logging

logging.basicConfig(filename='siterm.log', level=logging.DEBUG)
config = {}
with open("../config_cloud/config.yml", 'r') as f:
    config = yaml.safe_load(f)
os.environ["X509_USER_KEY"] = config['ssl_certificate_key']
os.environ["X509_USER_CERT"] = config['ssl_certificate']

def getUTCnow():
    """Get UTC Time."""
    now = datetime.datetime.utcnow()
    timestamp = int(time.mktime(now.timetuple()))
    return timestamp


def node_data(data, id, gateway):
    siteMap = {}
    id = "rtmon-" + id
    visitedPort = {}
    for port in data['Ports']:
        if "Host" in port:
            node = {}
            node['hostname'] = port["Host"][0]["Name"].split(":")[-1]
            node["hosttype"] = "host"
            node["type"] = "prometheus-push"
            node["metadata"] = {}
            node["metadata"]["instance"] = port["Host"][0]["Name"]
            node["metadata"]["flow"] = id
            node["gateway"] = gateway
            node["runtime"] = str(int(time.time()) + 610)
            node["resolution"] = "5"
            if port["Site"] not in siteMap:
                siteMap[port["Site"]] = []
            new_node = copy.deepcopy(node)
            siteMap[port["Site"]].append(node)
            new_node["type"] = "arp-push"
            siteMap[port["Site"]].append(new_node)

    for port in data["Ports"]:
        if port["Node"] not in visitedPort:
            node = {}
            node['hostname'] = port["Node"].split(":")[-1]
            node["hosttype"] = "switch"
            node["type"] = "prometheus-push"
            node["metadata"] = {}
            node["metadata"]["instance"] = port["Node"]
            node["metadata"]["flow"] = id
            node["gateway"] = gateway
            node["runtime"] = str(int(time.time()) + 610)
            node["resolution"] = "5"
            if port["Site"] not in siteMap:
                siteMap[port["Site"]] = []
            siteMap[port["Site"]].append(node)
            visitedPort[port["Node"]] = 1
    
    return siteMap
def makeRequest(cls, url, params):
 
    """Make HTTP Request"""
    ver = params.get('verb')
    logging.info("\033[32m" + f'{ver} : {url}' + "\033[0m")
    print("\033[32m" + f'{ver} : {url}' + "\033[0m")

    cert=(os.environ["X509_USER_CERT"], os.environ["X509_USER_KEY"])
    
    
    if params.get('verb') == 'GET':
        out = requests.get(url, cert=cert, verify=False)
    elif params.get('verb') == 'POST':
        out = requests.post(url, cert=cert, json=params.get('data', {}), verify=False)
    elif params.get('verb') == 'PUT':
        out = requests.put(url, cert=cert, json=params.get('data', {}), verify=False)
    #pprint.pprint(json.loads(out.text))
    #print(json.loads(out.text))
    # print(out)
    if out.ok == False:
        logging.info("\033[31m" + f'{ver} : {url}' + "\033[0m")
        print("\033[31m" + f'{ver} : {url}' + "\033[0m")
    return json.loads(out.text), out.ok, out

def debugActions(cls, dataIn, dataUpd):
    """Test Debug Actions: submit, get update"""
    # SUBMIT
    urls = f"{cls.baseURL}/submitdebug/NEW"
    
    outs = makeRequest(cls, urls, {'verb': 'POST', 'data': dataIn})
    # GET
    urlg = f"{cls.baseURL}/getdebug/{outs[0]['ID']}"
    makeRequest(cls, urlg, {'verb': 'GET', 'data': {}})
    
    # UPDATE
    urlu = f"{cls.baseURL}/updatedebug/{outs[0]['ID']}"
    
    makeRequest(cls, urlu, {'verb': 'PUT', 'data': dataUpd})

class SiteRMAPI():
    def __init__(self, baseURL, node_data):
        self.baseURL = baseURL
        self.node_data = node_data
    def test(self, node_data):
        for data in node_data:
            outsuc = {"out": ["running"], "err": "", "exitCode": 0}
            dataupd = {'state': 'active', 'output': json.dumps(outsuc)}
            debugActions(self, data, dataupd)
            #? why this?
            url = f"{self.baseURL}/getalldebughostnameactive/dummyhostname"
            makeRequest(self, url, {'verb': 'GET', 'data': {}})


#data = {}
#with open("manifest.json", 'r') as f:
#    data = json.load(f)
#config = {}
#with open("../config_cloud/config.yml", 'r') as f:
#    config = yaml.safe_load(f)
#siteMap = node_data(data, "4700d4e0-bb7d-4a30-9736-91fa5f2f1852", config["pushgateway"])

#with open("test_node.json", 'w') as f:
#    json.dump(siteMap, f, indent=2)
#for idMap in siteMap.keys():
#    if idMap in config['siterm_url_map']:
#        baseURL = config['siterm_url_map'][f'{idMap}']
#        api = SiteRMAPI(baseURL, node_data=siteMap[idMap])
       
#        api.test(siteMap[idMap])
#    else:
#        print(f'This Key: {idMap} does not exist in config.yml')
#print("Data Dispatched")


