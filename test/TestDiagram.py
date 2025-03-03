import os
import time
from DiagramWorker import *

import glob


import json

# File paths
self_order_file = "/Users/sunami/Desktop/SenseMar/sense-rtmon/test/multipoint.json"
instance = {'intents': [{'id': '3843232f-c610-4ef2-9129-e78cb655d300', 'json': {'service_instance_uuid': 'dd030052-6156-4c5d-b53e-c388d948669d', 'data': {'type': 'Multi-Point VLAN Bridge', 'connections': [{'bandwidth': {'qos_class': 'guaranteedCapped', 'capacity': '1000'}, 'name': 'Connection 1', 'ip_address_pool': {'netmask': '/64', 'name': 'AutoGOLE-Test-IPv6-Pool'}, 'terminals': [{'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:node-2-9.sdsc.optiputer.net'}, {'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:node-2-10.sdsc.optiputer.net'}, {'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:sn3700_s0:Ethernet72'}], 'path_profile': {'inclusion_list': [{'uri': 'urn:ogf:network:nrp-nautilus.io:2020:edgecore_s0'}]}, 'assign_debug_ip': True}]}, 'service': 'dnc', 'options': [], 'service_profile_uuid': '911264ea-29ad-4615-8398-b7b578e976f2', 'queries': []}, 'provisioned': True, 'serviceInstanceUUID': 'dd030052-6156-4c5d-b53e-c388d948669d', 'serviceDeltaUUID': 'a8fc434b-6145-47c3-adc0-ae606d24bd8e', 'creation_time': '2025-02-19 18:14:23'}], 'alias': 'sunami-multipoint 4', 'referenceUUID': 'dd030052-6156-4c5d-b53e-c388d948669d', 'profileUUID': '911264ea-29ad-4615-8398-b7b578e976f2', 'state': 'CREATE - READY', 'owner': 'jbalcas@caltech.edu', 'lastState': 'COMMITTED', 'timestamp': '2025/02/19 18:14:22', 'archived': False}

try:

    with open(self_order_file, 'r') as self_file:
        self_order = json.load(self_file)
    print("Loaded self_order:")
    print(json.dumps(self_order, indent=2))  # Pretty print for readability

    DiagramWorker(instance).createGraph("/Users/sunami/Desktop/SenseFeb/sense-rtmon/test/myimage", self_order)

except Exception as e:
    print(f"Error loading or processing files: {e}")
