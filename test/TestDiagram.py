import os
import time
from DiagramWorker import *

import glob


import json

# File paths
original_args_file = "/Users/sunami/Desktop/publish/sense-rtmon/autogole-api/original_argsdiagram_555da2e2-0c40-4e6d-b819-262515a05571.json"
self_order_file = "/Users/sunami/Desktop/publish/sense-rtmon/autogole-api/selfOrderdiagram_555da2e2-0c40-4e6d-b819-262515a05571.json"
kwargs = {'state': 'submitted', 'referenceUUID': '0a303274-a293-4af8-88b7-5b010d23a0f7', 'orchestrator': 'sense-o-dev.es.net', 'submission': 'AUTH_KEY', 'instance': {'intents': [{'id': '5d86903e-6b09-4c61-8cca-4d7e36c9aa1a', 'json': {'service_instance_uuid': '0a303274-a293-4af8-88b7-5b010d23a0f7', 'data': {'type': 'Multi-Path P2P VLAN', 'connections': [{'bandwidth': {'qos_class': 'bestEffort'}, 'name': 'Connection 1', 'ip_address_pool': {'netmask': '/30', 'name': 'AutoGOLE-IPv4-Test-Pool'}, 'terminals': [{'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:ultralight.org:2013:sandie-7.ultralight.org'}, {'vlan_tag': 'any', 'assign_ip': True, 'uri': 'urn:ogf:network:nrp-nautilus.io:2020:k8s-gen5-01.sdsc.optiputer.net'}]}]}, 'service': 'dnc', 'options': [], 'service_profile_uuid': '49d722dc-2f8f-49f9-a7ab-92c2f26822ed', 'queries': []}, 'provisioned': True, 'serviceInstanceUUID': '0a303274-a293-4af8-88b7-5b010d23a0f7', 'serviceDeltaUUID': 'e7787217-f1e5-41e1-941d-0a63ad66ba40', 'creation_time': '2024-11-04 06:49:00'}], 'alias': 'RTMON-IT6-Caltech-SDSC', 'referenceUUID': '0a303274-a293-4af8-88b7-5b010d23a0f7', 'profileUUID': '49d722dc-2f8f-49f9-a7ab-92c2f26822ed', 'state': 'REINSTATE - READY', 'owner': 'sdasgupta@lbl.gov', 'lastState': 'COMMITTED', 'timestamp': '2024/10/22 16:17:47', 'archived': False}, 'manifest': {'Ports': [{'Site': 'urn:ogf:network:nrp-nautilus.io:2020', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:nrp-nautilus.io:2020:edgecore_s0:Ethernet32', 'IPv4': '?port_ipv4?', 'Node': 'T2_US_SDSC:edgecore_s0', 'Peer': '?peer?', 'Host': [{'IPv6': '?ipv6?', 'IPv4': '10.251.86.138/30', 'Interface': 'enp168s0np0', 'Mac': 'a0:88:c2:86:ee:7c', 'Name': 'T2_US_SDSC:k8s-gen5-01.sdsc.optiputer.net'}], 'Vlan': '3607', 'Mac': '00:90:fb:76:e4:7b', 'Name': 'Ethernet32'}, {'Site': 'urn:ogf:network:nrp-nautilus.io:2020', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:nrp-nautilus.io:2020:edgecore_s0:PortChannel500', 'IPv4': '?port_ipv4?', 'Node': 'T2_US_SDSC:edgecore_s0', 'Peer': 'urn:ogf:network:sense-oasis-nrp-nautilus.io:2020:oasis:Pc500', 'Vlan': '3607', 'Mac': '00:90:fb:76:e4:7b', 'Name': 'PortChannel500'}, {'Site': 'urn:ogf:network:ultralight.org:2013', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:ultralight.org:2013:dellos9_s0:Port-channel_103', 'IPv4': '?port_ipv4?', 'Node': 'T2_US_Caltech_Test:dellos9_s0', 'Peer': 'urn:ogf:network:tier2.ultralight.org:2024:dellos10_s0:Port-channel_101', 'Vlan': '3607', 'Mac': '4c:76:25:e8:44:c2', 'Name': 'Port-channel 103'}, {'Site': 'urn:ogf:network:ultralight.org:2013', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:ultralight.org:2013:dellos9_s0:hundredGigE_1-32', 'IPv4': '?port_ipv4?', 'Node': 'T2_US_Caltech_Test:dellos9_s0', 'Peer': '?peer?', 'Host': [{'IPv6': '?ipv6?', 'IPv4': '10.251.86.137/30', 'Interface': 'mlx5p1s1', 'Mac': 'ec:0d:9a:c1:ba:60', 'Name': 'T2_US_Caltech_Test:sandie-7.ultralight.org'}], 'Vlan': '3607', 'Mac': '4c:76:25:e8:44:c2', 'Name': 'hundredGigE 1/32'}, {'Site': 'urn:ogf:network:sc-test.cenic.net:2020', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:sc-test.cenic.net:2020:aristaeos_s0:Port-Channel502', 'IPv4': '?port_ipv4?', 'Node': 'NRM_CENIC:aristaeos_s0', 'Peer': 'urn:ogf:network:sense-oasis-nrp-nautilus.io:2020:oasis:Pc502', 'Vlan': '3607', 'Mac': '28:e7:1d:3f:53:70', 'Name': 'Port-Channel502'}, {'Site': 'urn:ogf:network:sc-test.cenic.net:2020', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:sc-test.cenic.net:2020:aristaeos_s0:Port-Channel501', 'IPv4': '?port_ipv4?', 'Node': 'NRM_CENIC:aristaeos_s0', 'Peer': 'urn:ogf:network:tier2.ultralight.org:2024:dellos10_s0:Port-channel_102', 'Vlan': '3607', 'Mac': '28:e7:1d:3f:53:88', 'Name': 'Port-Channel501'}, {'Site': 'urn:ogf:network:tier2.ultralight.org:2024', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:tier2.ultralight.org:2024:dellos10_s0:Port-channel_101', 'IPv4': '?port_ipv4?', 'Node': 'T2_US_Caltech:dellos10_s0', 'Peer': 'urn:ogf:network:ultralight.org:2013:dellos9_s0:Port-channel_103', 'Vlan': '3607', 'Mac': '8c:04:ba:e9:0e:a8', 'Name': 'Port-channel 101'}, {'Site': 'urn:ogf:network:tier2.ultralight.org:2024', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:tier2.ultralight.org:2024:dellos10_s0:Port-channel_102', 'IPv4': '?port_ipv4?', 'Node': 'T2_US_Caltech:dellos10_s0', 'Peer': 'urn:ogf:network:sc-test.cenic.net:2020:aristaeos_s0:Port-Channel501', 'Vlan': '3607', 'Mac': '8c:04:ba:e9:0e:a9', 'Name': 'Port-channel 102'}, {'Site': 'urn:ogf:network:sense-oasis-nrp-nautilus.io:2020', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:sense-oasis-nrp-nautilus.io:2020:oasis:Pc500', 'IPv4': '?port_ipv4?', 'Node': 'T2_US_UCSD_OASIS:oasis', 'Peer': 'urn:ogf:network:nrp-nautilus.io:2020:edgecore_s0:PortChannel500', 'Vlan': '3607', 'Mac': '?port_mac?', 'Name': 'Pc500'}, {'Site': 'urn:ogf:network:sense-oasis-nrp-nautilus.io:2020', 'IPv6': '?port_ipv6?', 'Port': 'urn:ogf:network:sense-oasis-nrp-nautilus.io:2020:oasis:Pc502', 'IPv4': '?port_ipv4?', 'Node': 'T2_US_UCSD_OASIS:oasis', 'Peer': 'urn:ogf:network:sc-test.cenic.net:2020:aristaeos_s0:Port-Channel502', 'Vlan': '3607', 'Mac': '?port_mac?', 'Name': 'Pc502'}]}}

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

    DiagramWorker(**kwargs).createGraph("/Users/sunami/Desktop/publish/sense-rtmon/autogole-api/src/python/RTMonLibs/myimage", self_order)

except Exception as e:
    print(f"Error loading or processing files: {e}")
