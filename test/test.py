import os
import time
from DiagramWorker import *

import glob


import json

# File paths
self_order_file = ["/test/Debug.json", "/test/NRP.json", "/test/BGP.json"]
instance = [
{'intents': [{'id': 'da2fc17b-2fa5-46e8-9cdb-d0732c709eb9', 'json': {'service_instance_uuid': '3fa68210-35d1-4df6-8e02-dad45bccdcfd', 'data': {'type': 'Multi-Path P2P VLAN', 'connections': [{'bandwidth': {'qos_class': 'guaranteedCapped', 'capacity': '1000'}, 'name': 'Connection 1', 'ip_address_pool': {'netmask': '/64', 'name': 'AutoGOLE-Test-IPv6-Pool'}, 'terminals': [{'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:k8s-gen5-01.sdsc.optiputer.net:enp168s0np0'}, {'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:node-2-6.sdsc.optiputer.net'}], 'path_profile': {'inclusion_list': [{'uri': 'urn:ogf:network:nrp-nautilus.io:2020:edgecore_s0'}]}, 'assign_debug_ip': True}]}, 'service': 'dnc', 'options': [], 'service_profile_uuid': '036ecbe8-95dc-4a3d-b339-4ddc5249962b', 'queries': []}, 'provisioned': True, 'serviceInstanceUUID': '3fa68210-35d1-4df6-8e02-dad45bccdcfd', 'serviceDeltaUUID': '07a35bc2-5888-49e1-9c46-ed8889a64474', 'creation_time': '2025-02-12 18:42:33'}], 'alias': 'sunami-debug-ip 4', 'referenceUUID': '3fa68210-35d1-4df6-8e02-dad45bccdcfd', 'profileUUID': '036ecbe8-95dc-4a3d-b339-4ddc5249962b', 'state': 'CREATE - READY', 'owner': 'jbalcas@caltech.edu', 'lastState': 'COMMITTED', 'timestamp': '2025/02/12 18:42:33', 'archived': False}
,

{'intents': [{'id': 'e14df4e8-db53-469e-bb98-ab41fec9bf4f', 'json': {'service_instance_uuid': '1a9129b2-841d-40dd-b5ce-d0753aa1cdc4', 'data': {'type': 'Multi-Path P2P VLAN', 'connections': [{'bandwidth': {'qos_class': 'guaranteedCapped', 'capacity': '1000'}, 'name': 'Connection 1', 'ip_address_pool': {'netmask': '/64', 'name': 'AutoGOLE-IPv6-Test-Pool'}, 'terminals': [{'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:k8s-gen5-01.sdsc.optiputer.net'}, {'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:k8s-gen5-02.sdsc.optiputer.net'}]}]}, 'service': 'dnc', 'options': [], 'service_profile_uuid': '20523347-8dda-42ff-a05c-265d4b6f354c', 'queries': []}, 'provisioned': True, 'serviceInstanceUUID': '1a9129b2-841d-40dd-b5ce-d0753aa1cdc4', 'serviceDeltaUUID': '934b44d4-7b12-45d0-a188-5b9833948891', 'creation_time': '2025-01-29 21:10:48'}], 'alias': 'NRP-Gen5-1-2 IPv6', 'referenceUUID': '1a9129b2-841d-40dd-b5ce-d0753aa1cdc4', 'profileUUID': '20523347-8dda-42ff-a05c-265d4b6f354c', 'state': 'CREATE - READY', 'owner': 'admin', 'lastState': 'COMMITTED', 'timestamp': '2025/01/29 21:10:47', 'archived': False}
,

{'intents': [{'id': 'ef463a7d-314d-46eb-9838-54e82e4a563f', 'json': {'service_instance_uuid': '88089fe4-a79c-4cee-b402-da2a9d98e3a7', 'data': {'type': 'Site-L3 over P2P VLAN', 'connections': [{'bandwidth': {'qos_class': 'guaranteedCapped', 'capacity': '1000'}, 'name': 'Connection 1', 'ip_address_pool': {'netmask': '/64', 'name': 'AutoGOLE-Test-IPv6-Pool'}, 'terminals': [{'vlan_tag': 'any', 'assign_ip': True, 'ipv6_prefix_list': '2620:6a:0:2842::/64', 'uri': 'urn:ogf:network:fnal.gov:2023'}, {'vlan_tag': 'any', 'assign_ip': True, 'ipv6_prefix_list': '2001:48d0:3001:111::/64', 'uri': 'urn:ogf:network:nrp-nautilus.io:2020'}], 'path_profile': {'exclusion_list': [{'uri': 'urn:ogf:network:stack-fabric:2024:topology'}]}}]}, 'service': 'dnc', 'options': [], 'service_profile_uuid': '17f3c81f-a080-44ca-b31d-aed863b122bc', 'queries': []}, 'provisioned': True, 'serviceInstanceUUID': '88089fe4-a79c-4cee-b402-da2a9d98e3a7', 'serviceDeltaUUID': 'a2ab2b17-8ff4-42a5-8882-337e3a8cf27d', 'creation_time': '2025-02-10 18:10:49'}], 'alias': 'sunami-bgp 3', 'referenceUUID': '88089fe4-a79c-4cee-b402-da2a9d98e3a7', 'profileUUID': '17f3c81f-a080-44ca-b31d-aed863b122bc', 'state': 'CREATE - READY', 'owner': 'sdasgupta@lbl.gov', 'lastState': 'COMMITTED', 'timestamp': '2025/02/10 18:10:48', 'archived': False}
,
{'intents': [{'id': '3843232f-c610-4ef2-9129-e78cb655d300', 'json': {'service_instance_uuid': 'dd030052-6156-4c5d-b53e-c388d948669d', 'data': {'type': 'Multi-Point VLAN Bridge', 'connections': [{'bandwidth': {'qos_class': 'guaranteedCapped', 'capacity': '1000'}, 'name': 'Connection 1', 'ip_address_pool': {'netmask': '/64', 'name': 'AutoGOLE-Test-IPv6-Pool'}, 'terminals': [{'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:node-2-9.sdsc.optiputer.net'}, {'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:node-2-10.sdsc.optiputer.net'}, {'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:sn3700_s0:Ethernet72'}], 'path_profile': {'inclusion_list': [{'uri': 'urn:ogf:network:nrp-nautilus.io:2020:edgecore_s0'}]}, 'assign_debug_ip': True}]}, 'service': 'dnc', 'options': [], 'service_profile_uuid': '911264ea-29ad-4615-8398-b7b578e976f2', 'queries': []}, 'provisioned': True, 'serviceInstanceUUID': 'dd030052-6156-4c5d-b53e-c388d948669d', 'serviceDeltaUUID': 'a8fc434b-6145-47c3-adc0-ae606d24bd8e', 'creation_time': '2025-02-19 18:14:23'}], 'alias': 'sunami-multipoint 4', 'referenceUUID': 'dd030052-6156-4c5d-b53e-c388d948669d', 'profileUUID': '911264ea-29ad-4615-8398-b7b578e976f2', 'state': 'CREATE - READY', 'owner': 'jbalcas@caltech.edu', 'lastState': 'COMMITTED', 'timestamp': '2025/02/19 18:14:22', 'archived': False}
]
name = ["debug", "NRP", "BGP", "multipoint"]
# Load the JSON data
for i in range(len(instance)):

    try:
        with open(self_order_file[i], 'r') as self_file:
            self_order = json.load(self_file)
        print("Loaded self_order:")
        print(json.dumps(self_order, indent=2))  # Pretty print for readability

        DiagramWorker(instance[i]).createGraph(f'/test/myimage_{name[i]}', self_order)

    except Exception as e:
        print(f"Error loading or processing files: {e}")
