import subprocess
import logging
import time
import json
import sys
import requests
import re 
import os
import glob
import datetime
from time import gmtime, strftime
#from converter import orchestratorConvert
from sense.client.workflow_combined_api import WorkflowCombinedApi
from sense.client.discover_api import DiscoverApi
# from generate_s import *
from dynamic import *
# from dispatch import *
from converter import converter
from nodePatch import *
logging.basicConfig(filename='output.log', level=logging.DEBUG)

def create_manifest(instance):
    template = {
        "Ports": [
            {
                "Port": "?terminal?",
                "Name": "?port_name?",
                "Vlan": "?vlan?",
                "Node": "?node_name?",
                "Peer": "?peer?",
                "Site": "?site?",
                "Host": [
                    {
                        "Name": "?host_name?",
                        "Interface": "?host_port_name?",
                        "IPv4": "?ipv4?",
                        "sparql": "SELECT DISTINCT ?host_port ?ipv4 WHERE { ?vlan_port nml:isAlias ?host_vlan_port. ?host_port nml:hasBidirectionalPort ?host_vlan_port. OPTIONAL { ?host_vlan_port mrs:hasNetworkAddress  ?ipv4na. ?ipv4na mrs:type \"ipv4-address\". ?ipv4na mrs:value ?ipv4.} }",
                        "sparql-ext": "SELECT DISTINCT ?host_name ?host_port_name  WHERE {?host a nml:Node. ?host nml:hasBidirectionalPort ?host_port. OPTIONAL {?host nml:name ?host_name.} OPTIONAL {?host_port mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?host_port_name.} }",
                        "required": "false"
                    }
                ],
                "sparql": "SELECT DISTINCT  ?vlan_port  ?vlan  WHERE { ?subnet a mrs:SwitchingSubnet. ?subnet nml:hasBidirectionalPort ?vlan_port. ?vlan_port nml:hasLabel ?vlan_l. ?vlan_l nml:value ?vlan. }",
                "sparql-ext": "SELECT DISTINCT ?terminal ?port_name ?node_name ?peer ?site WHERE { {?node a nml:Node. ?node nml:name ?node_name. ?node nml:hasBidirectionalPort ?terminal.  ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL {?terminal mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?port_name.} OPTIONAL {?terminal nml:isAlias ?peer.} OPTIONAL {?site nml:hasNode ?node.} OPTIONAL {?site nml:hasTopology ?sub_site. ?sub_site nml:hasNode ?node.} } UNION { ?site a nml:Topology. ?site nml:name ?node_name. ?site nml:hasBidirectionalPort ?terminal. ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL {?terminal mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?port_name.} OPTIONAL {?terminal nml:isAlias ?peer.}}}",
                "required": "true"
            }
        ]
    }
    workflowApi = WorkflowCombinedApi()
    print(f'workflowAPI: {workflowApi}')
    workflowApi.si_uuid = instance['referenceUUID']
    print(f' workflowApi.si_uuid : {workflowApi.si_uuid}')
    response = workflowApi.manifest_create(json.dumps(template))
    print(f'response: {response}')
    json_response = json.loads(response)
    print(f'json_response: {json_response}')
    manifest = json.loads(json_response['jsonTemplate'])
    print(f'manifest: {manifest}')
    logging.info("Manifest Created")
    

    return manifest

data={}

with open("data_filtered.json", 'r') as f:
    data = json.load(f)
for node in data:
    data = create_manifest(node)

print(data)
