#!/usr/bin/env python3
"""
Class for interacting with SENSE-0 API
"""
import copy
import os

from sense.client.workflow_combined_api import WorkflowCombinedApi
from sense.client.discover_api import DiscoverApi
from RTMonLibs.GeneralLibs import loadJson, dumpJson
from RTMonLibs.GeneralLibs import SENSEOFailure


class SenseAPI:
    """Class for interacting with SENSE-0 API"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        # Clients will be loaded by reloadClient
        self.workflow_apis = {}
        self.discover_apis = {}

    def s_reloadClient(self):
        """Load SENSE-0 client"""
        if os.environ.get('SENSE_AUTH_OVERRIDE_NAME') and \
                (os.environ.get('SENSE_AUTH_OVERRIDE_NAME') not in self.workflow_apis or \
                 os.environ.get('SENSE_AUTH_OVERRIDE_NAME') not in self.discover_apis):
            self.workflow_apis[os.environ['SENSE_AUTH_OVERRIDE_NAME']] = WorkflowCombinedApi()
            self.discover_apis[os.environ['SENSE_AUTH_OVERRIDE_NAME']] = DiscoverApi()

    def s_getWorkflowApi(self):
        """Get Workflow API"""
        orchestrator = os.environ.get('SENSE_AUTH_OVERRIDE_NAME')
        if orchestrator in self.workflow_apis:
            return self.workflow_apis[orchestrator]
        raise Exception(f"Orchestrator {orchestrator} not found in the list of clients")

    def s_getDiscoverApi(self):
        """Get Discover API"""
        orchestrator = os.environ.get('SENSE_AUTH_OVERRIDE_NAME')
        if orchestrator in self.discover_apis:
            return self.discover_apis[orchestrator]
        raise Exception(f"Orchestrator {orchestrator} not found in the list of clients")


    def s_getManifest(self, instance):
        """Create a manifest in SENSE-0"""
        template = {"Ports": [{
              "Port": "?terminal?",
              "Name": "?port_name?",
              "Vlan": "?vlan?",
              "Mac": "?port_mac?",
              "IPv6": "?port_ipv6?",
              "IPv4": "?port_ipv4?",
              "Node": "?node_name?",
              "Peer": "?peer?",
              "Site": "?site?",
              "Host": [
                {
                  "Interface": "?host_port_name?",
                  "Name": "?host_name?",
                  "IPv4": "?ipv4?",
                  "IPv6": "?ipv6?",
                  "Mac": "?mac?",
                  "sparql": "SELECT DISTINCT ?host_port ?ipv4 ?ipv6 ?mac WHERE { ?host_vlan_port nml:isAlias ?vlan_port. ?host_port nml:hasBidirectionalPort ?host_vlan_port. OPTIONAL {?host_vlan_port mrs:hasNetworkAddress  ?ipv4na. ?ipv4na mrs:type \"ipv4-address\". ?ipv4na mrs:value ?ipv4.} OPTIONAL {?host_vlan_port mrs:hasNetworkAddress  ?ipv6na. ?ipv6na mrs:type \"ipv6-address\". ?ipv6na mrs:value ?ipv6.} OPTIONAL {?host_vlan_port mrs:hasNetworkAddress  ?macana. ?macana mrs:type \"mac-address\". ?macana mrs:value ?mac.} FILTER NOT EXISTS {?sw_svc mrs:providesSubnet ?vlan_subnt. ?vlan_subnt nml:hasBidirectionalPort ?host_vlan_port.} }",
                  "sparql-ext": "SELECT DISTINCT ?host_name ?host_port_name  WHERE {?host a nml:Node. ?host nml:hasBidirectionalPort ?host_port. OPTIONAL {?host nml:name ?host_name.} OPTIONAL {?host_port mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?host_port_name.} }",
                  "required": "false"
                }
              ],
              "sparql": "SELECT DISTINCT  ?vlan_port  ?vlan  WHERE { ?subnet a mrs:SwitchingSubnet. ?subnet nml:hasBidirectionalPort ?vlan_port. ?vlan_port nml:hasLabel ?vlan_l. ?vlan_l nml:value ?vlan. }",
              "sparql-ext": "SELECT DISTINCT ?terminal ?port_name ?node_name ?peer ?site ?port_mac ?port_ipv4 ?port_ipv6 WHERE { { ?node a nml:Node. ?node nml:name ?node_name. ?node nml:hasBidirectionalPort ?terminal. ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL { ?terminal mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?port_name. } OPTIONAL { ?terminal nml:isAlias ?peer. } OPTIONAL { ?site nml:hasNode ?node. } OPTIONAL { ?site nml:hasTopology ?sub_site. ?sub_site nml:hasNode ?node. } OPTIONAL { ?terminal mrs:hasNetworkAddress ?naportmac. ?naportmac mrs:type \"mac-address\". ?naportmac mrs:value ?port_mac. } OPTIONAL { ?vlan_port mrs:hasNetworkAddress ?ipv4na. ?ipv4na mrs:type \"ipv4-address\". ?ipv4na mrs:value ?port_ipv4. } OPTIONAL { ?vlan_port mrs:hasNetworkAddress ?ipv6na. ?ipv6na mrs:type \"ipv6-address\". ?ipv6na mrs:value ?port_ipv6. } } UNION { ?site a nml:Topology. ?site nml:name ?node_name. ?site nml:hasBidirectionalPort ?terminal. ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL { ?terminal mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?port_name. } OPTIONAL { ?terminal nml:isAlias ?peer. } OPTIONAL { ?terminal mrs:hasNetworkAddress ?naportmac. ?naportmac mrs:type \"mac-address\". ?naportmac mrs:value ?port_mac. } OPTIONAL { ?vlan_port mrs:hasNetworkAddress ?ipv4na. ?ipv4na mrs:type \"ipv4-address\". ?ipv4na mrs:value ?port_ipv4. } OPTIONAL { ?vlan_port mrs:hasNetworkAddress ?ipv6na. ?ipv6na mrs:type \"ipv6-address\". ?ipv6na mrs:value ?port_ipv6. } } }",
              "required": "true"
            }
          ]
        }
        wApi = self.s_getWorkflowApi()
        wApi.si_uuid = instance['referenceUUID']
        response = wApi.manifest_create(dumpJson(template, self.logger))
        json_response = loadJson(response, self.logger)
        if 'jsonTemplate' not in json_response:
            self.logger.debug(f"WARNING: {instance['referenceUUID']} did not receive correct output!")
            self.logger.debug(f"WARNING: Response: {response}")
            return {}
        manifest = loadJson(json_response['jsonTemplate'], self.logger)
        return manifest

    def s_getInstances(self):
        """Get all instances from SENSE-0"""
        response = None
        try:
            dApi = self.s_getDiscoverApi()
            response = dApi.discover_service_instances_get()
        except Exception as ex:
            self.logger.critical(f'API Call Failed!. Exception {ex} Response: {response}')
            raise SENSEOFailure(f'API Call Failed!. Exception {ex} Response: {response}') from ex
        if not response:
            self.logger.error("No Data received from SENSE-O")
            return {}
        # SENSE-O returns str json key - which we need to load and make it a dict
        out = []
        for item in loadJson(response, self.logger).get('instances', []):
            tmpIntents = copy.deepcopy(item['intents'])
            item['intents'] = []
            for intent in tmpIntents:
                if 'json' in intent and isinstance(intent['json'], str):
                    intent['json'] = loadJson(intent['json'], self.logger)
                item['intents'].append(intent)
            out.append(item)
        return out

    def s_getInstance(self, instance_uuid):
        """Get instance by UUID"""
        instances = self.s_getInstances()
        for instance in instances:
            if 'referenceUUID' in instance and instance['referenceUUID'] == instance_uuid:
                return instance
        return {}
