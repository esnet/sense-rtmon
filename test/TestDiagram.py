import os
import time
from DiagramWorker import *

import glob


import json

# File paths
original_args_file = "/Users/sunami/Desktop/publish/sense-rtmon/autogole-api/original_argsdiagram_555da2e2-0c40-4e6d-b819-262515a05571.json"
self_order_file = "/Users/sunami/Desktop/SenseFeb/sense-rtmon/test/sunami-debug-instance.json"
instance = {'intents': [{'id': '3632aabc-5c39-4541-ac53-e53cf5aba536', 'json': {'service_instance_uuid': '0d0f630f-b147-4180-85c1-49afad792c3a', 'data': {'type': 'Multi-Path P2P VLAN', 'connections': [{'bandwidth': {'qos_class': 'guaranteedCapped', 'capacity': '1000'}, 'name': 'Connection 1', 'ip_address_pool': {'netmask': '/64', 'name': 'AutoGOLE-Test-IPv6-Pool'}, 'terminals': [{'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:k8s-gen5-01.sdsc.optiputer.net:enp168s0np0'}, {'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:k8s-gen5-02.sdsc.optiputer.net:enp168s0np0'}], 'path_profile': {'inclusion_list': [{'uri': 'urn:ogf:network:nrp-nautilus.io:2020:edgecore_s0'}]}, 'assign_debug_ip': True}]}, 'service': 'dnc', 'options': [], 'service_profile_uuid': '036ecbe8-95dc-4a3d-b339-4ddc5249962b', 'queries': []}, 'provisioned': True, 'serviceInstanceUUID': '0d0f630f-b147-4180-85c1-49afad792c3a', 'serviceDeltaUUID': '57e39e4a-4bf5-4e12-913f-1c0a619306c8', 'creation_time': '2025-02-04 23:43:36'}], 'alias': 'sunami-debug-ip', 'referenceUUID': '0d0f630f-b147-4180-85c1-49afad792c3a', 'profileUUID': '036ecbe8-95dc-4a3d-b339-4ddc5249962b', 'state': 'CREATE - READY', 'owner': 'jbalcas@caltech.edu', 'lastState': 'COMMITTED', 'timestamp': '2025/02/04 23:43:35', 'archived': False}
# Load the JSON data
try:
    with open(original_args_file, 'r') as orig_file:
        original_args = json.load(orig_file)
    print("Loaded original_args:")
    print(json.dumps(original_args, indent=2))  # Pretty print for readability

    with open(self_order_file, 'r') as self_file:
        self_order = json.load(self_file)
    print("Loaded self_order:")
    print(json.dumps(self_order, indent=2))  # Pretty print for readability

    DiagramWorker(instance).createGraph("/Users/sunami/Desktop/SenseFeb/sense-rtmon/test/myimage", self_order)

except Exception as e:
    print(f"Error loading or processing files: {e}")
