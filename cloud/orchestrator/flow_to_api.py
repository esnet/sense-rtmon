"""Test Debug Prometheus Push"""
import yaml
import sys
import os
import time
import datetime
import requests
import pprint
import simplejson as json

os.environ["X509_USER_KEY"] = '/root/sense-o.es.net-ssl/sense-o.key'
os.environ["X509_USER_CERT"] = '/root/sense-o.es.net-ssl/sense-o.crt'


def getUTCnow():
    """Get UTC Time."""
    now = datetime.datetime.utcnow()
    timestamp = int(time.mktime(now.timetuple()))
    return timestamp

def makeRequest(cls, url, params):
    """Make HTTP Request"""
    url = f"{cls.hostname}{url}"
    cert=(os.environ["X509_USER_CERT"], os.environ["X509_USER_KEY"])
    if params.get('verb') == 'GET':
        out = requests.get(url, cert=cert, verify=False)
    elif params.get('verb') == 'POST':
        out = requests.post(url, cert=cert, json=params.get('data', {}), verify=False)
    elif params.get('verb') == 'PUT':
        out = requests.put(url, cert=cert, json=params.get('data', {}), verify=False)
    pprint.pprint(json.loads(out.text))
    return json.loads(out.text), out.ok, out


def debugActions(cls, dataIn, dataUpd):
    """Test Debug Actions: submit, get update"""
    # SUBMIT
    urls = f"/{cls.sitename}/sitefe/json/frontend/submitdebug/NEW"
    outs = makeRequest(cls, urls, {'verb': 'POST', 'data': dataIn})
    # GET
    urlg = f"/{cls.sitename}/sitefe/json/frontend/getdebug/{outs[0]['ID']}"
    makeRequest(cls, urlg, {'verb': 'GET', 'data': {}})
    # UPDATE
    urlu = f"/{cls.sitename}/sitefe/json/frontend/updatedebug/{outs[0]['ID']}"
    makeRequest(cls, urlu, {'verb': 'PUT', 'data': dataUpd})


class SiteRMAPI():
    def __init__(self, hostname, sitename, node_data):
        print(hostname, sitename)
        self.hostname = hostname
        self.sitename = sitename
        self.node_data = node_data

    def test(self):
        """Test Prometheus Push Debug API"""
        for data in node_data:
            outsuc = {"out": ["running"], "err": "", "exitCode": 0}
            dataupd = {'state': 'active', 'output': json.dumps(outsuc)}
            debugActions(self, data, dataupd)

            url = f"/{self.sitename}/sitefe/json/frontend/getalldebughostnameactive/dummyhostname"
            makeRequest(self, url, {'verb': 'GET', 'data': {}})

def read_file(filename):
    with open(f"../../config_flow/{filename}", 'r') as file:
        input_text = file.read()
        lines = input_text.split('\n')
        lines = [line for line in lines if not line.strip().startswith("#") and line.strip()]
        input_text_cleaned = '\n'.join(lines)
    return input_text_cleaned

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <config_filename>")
        sys.exit(1)

    filename = sys.argv[1]
    input_text_cleaned = read_file(filename)
    # Load the YAML data
    data = yaml.safe_load(input_text_cleaned)

    pushgateway_host = data['pushgateway']
    node_data = []

    for node in data['node']:
        sub_node = {
            'hostname': node['name'],
            'hosttype': node['type'],
            'type': 'prometheus-push',
            'metadata': {'instance': node['name'], 'sense_mon_id':  node['sense_mon_id']},
            'gateway': pushgateway_host,
            'runtime': str(int(getUTCnow())+node['runtime']),
            'resolution': '5'
        }
        node_data.append(sub_node)
        
        if node['type'] == 'host':
            if node['arp'] == 'on':
                sub_node['type'] = 'arp-push'
                node_data.append(sub_node)

        
    print (node_data)
    # params = {'hostname': 'https://sense-caltech-fe.sdn-lb.ultralight.org', 'sitename': 'T2_US_Caltech_Test'}
    # api = SiteRMAPI(**params,node_data=node_data)
    # api.test()
    
# for data in [{'hostname': 'sdn-dtn-1-7.ultralight.org', 'hosttype': 'host',
#             'type': 'prometheus-push', 'metadata': {'instance': 'sdn-dtn-1-7.ultralight.org', 'flow_id': 'unqiue_test_id'},
#             'gateway': 'dev2.virnao.com:9091', 'runtime': str(int(getUTCnow())+610),
#             'resolution': '5'},
#             {'hostname': 'sdn-dtn-1-7.ultralight.org', 'hosttype': 'host',
#             'type': 'arp-push', 'metadata': {'instance': 'sdn-dtn-1-7.ultralight.org'},
#             'gateway': 'dev2.virnao.com:9091', 'runtime': str(int(getUTCnow())+610),
#             'resolution': '5'},
#             {'hostname': 'dellos9_s0', 'hosttype': 'host',
#             'type': 'prometheus-push', 'metadata': {'instance': 'dellos9_s0'},
#             'gateway': 'dev2.virnao.com:9091', 'runtime': str(int(getUTCnow())+610),
#             'resolution': '5'}]: