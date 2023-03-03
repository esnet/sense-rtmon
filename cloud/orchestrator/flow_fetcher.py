import os
import json

from sense.client.workflow_combined_api import WorkflowCombinedApi
from sense.client.discover_api import DiscoverApi

import unittest

class TestFlowFetcher(unittest.TestCase):
    def setUp(self) -> None:
        discoverApi = DiscoverApi()
        response = discoverApi.discover_service_instances_get()
        if len(response) == 0 or "ERROR" in response:
            raise ValueError(f"Failed to fetch service instances")
        self.instances = []
        instances = json.loads(response)['instances']
        for ins in instances:
            self.instances.append(ins['referenceUUID'])

        self.template = """{
            "Ports": [
              {
                "Name": "?terminal?",
                "Vlan": "?vlan?",
                "Node": "?node_name?",
                "sparql": "SELECT DISTINCT  ?vlan_port  ?vlan  WHERE { ?subnet a mrs:SwitchingSubnet. ?subnet nml:hasBidirectionalPort ?vlan_port. ?vlan_port nml:hasLabel ?vlan_l. ?vlan_l nml:value ?vlan. }",
                "sparql-ext": "SELECT DISTINCT ?terminal ?node_name ?peer WHERE { {?node a nml:Node. ?node nml:name ?node_name. ?node nml:hasBidirectionalPort ?terminal. ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL {?terminal nml:isAlias ?peer.}} UNION { ?node a nml:Topology. ?node nml:name ?node_name. ?node nml:hasBidirectionalPort ?terminal. ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL {?terminal nml:isAlias ?peer.}}}",
                "required": "true",
                "Host": [
                 {
                   "Interface": "?host_port?",
                   "IP Address": "?ipv4?",
                    "sparql": "SELECT DISTINCT ?host_port ?ipv4 WHERE { ?vlan_port nml:isAlias ?host_vlan_port. ?host_port nml:hasBidirectionalPort ?host_vlan_port. ?host_vlan_port mrs:hasNetworkAddress  ?ipv4na. ?ipv4na mrs:type \\"ipv4-address\\". ?ipv4na mrs:value ?ipv4. }",
                    "required": "false"
                 }
                ],
                "Peer": "?peer?"
              }
            ]
        }"""

    def test_list_instances(self) -> None:
        print(self.instances)

    def test_fetch_manifests(self) -> None:
        workflowApi = WorkflowCombinedApi()
        for instance in self.instances:
            workflowApi.si_uuid = instance
            response = workflowApi.manifest_create(self.template)
            json_response = json.loads(response)
            print(json.dumps(json.loads(json_response['jsonTemplate']), indent=2))

