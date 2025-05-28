#!/usr/bin/env python3
# pylint: disable=no-member,line-too-long
"""
Class for interacting with SENSE-0 API
"""
import copy
import os
import uuid
import json
import time

from sense.client.workflow_combined_api import WorkflowCombinedApi
from sense.client.discover_api import DiscoverApi
from sense.client.task_api import TaskApi
from sense.client.metadata_api import MetadataApi
from RTMonLibs.GeneralLibs import loadJson, dumpJson
from RTMonLibs.GeneralLibs import SENSEOFailure
from RTMonLibs.GeneralLibs import getUTCnow


class SenseAPI:
    """Class for interacting with SENSE-0 API"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get("config")
        self.logger = kwargs.get("logger")
        # Clients will be loaded by reloadClient
        self.workflow_apis = {}
        self.discover_apis = {}
        self.task_apis = {}
        self.meta_apis = {}
        self.uuids = {}
        self.supported_actions = {
            "executeping": {
                "name": "Issue Ping between endpoints",
                "key": "executeping",
                "description": "Issue ping automatically between endpoints (Default true)",
                "type": "boolean",
                "default": True,
            },
            "allmacs": {
                "name": "Show All Learned Mac's",
                "key": "allmacs",
                "description": "Generate table in dashboard with all MAC addresses learned in the network devices (Default False)",
                "type": "boolean",
                "default": False,
            },
            "debugmode": {
                "name": "Debug Mode (Detailed graphs)",
                "key": "debugmode",
                "description": "Show more detailed dashboard with all debug information included (Default False)",
                "type": "boolean",
                "default": False,
            },
        }

    def _s_getworkeruuid(self):
        """Generate UUID"""
        orchestrator = os.environ.get("SENSE_AUTH_OVERRIDE_NAME")
        if orchestrator in self.uuids:
            return self.uuids[orchestrator]
        return str(uuid.uuid4())

    def s_reloadClient(self):
        """Load SENSE-0 client"""
        senseoname = os.environ.get("SENSE_AUTH_OVERRIDE_NAME")
        if senseoname not in self.workflow_apis:
            self.workflow_apis[senseoname] = WorkflowCombinedApi()
        if senseoname not in self.discover_apis:
            self.discover_apis[senseoname] = DiscoverApi()
        if senseoname not in self.task_apis:
            self.task_apis[senseoname] = TaskApi()
        if senseoname not in self.meta_apis:
            self.meta_apis[senseoname] = MetadataApi()
        if senseoname not in self.uuids:
            self.uuids[senseoname] = self._s_getworkeruuid()

    def s_getWorkflowApi(self):
        """Get Workflow API"""
        orchestrator = os.environ.get("SENSE_AUTH_OVERRIDE_NAME")
        if orchestrator in self.workflow_apis:
            return self.workflow_apis[orchestrator]
        raise Exception(f"Orchestrator {orchestrator} not found in the list of clients")

    def s_getDiscoverApi(self):
        """Get Discover API"""
        orchestrator = os.environ.get("SENSE_AUTH_OVERRIDE_NAME")
        if orchestrator in self.discover_apis:
            return self.discover_apis[orchestrator]
        raise Exception(f"Orchestrator {orchestrator} not found in the list of clients")

    def s_getTaskApi(self):
        """Get Task API"""
        orchestrator = os.environ.get("SENSE_AUTH_OVERRIDE_NAME")
        if orchestrator in self.task_apis:
            return self.task_apis[orchestrator]
        raise Exception(f"Orchestrator {orchestrator} not found in the list of clients")

    def s_getMetaApi(self):
        """Get Metadata API"""
        orchestrator = os.environ.get("SENSE_AUTH_OVERRIDE_NAME")
        if orchestrator in self.meta_apis:
            return self.meta_apis[orchestrator]
        raise Exception(f"Orchestrator {orchestrator} not found in the list of clients")

    def s_getMetadataRegData(self):
        """Get Metadata Registration Data"""
        folderName = self._getFolderName()
        data = {
            "name": folderName,
            "uuid": self._s_getworkeruuid(),
            "last_update": getUTCnow(),
        }
        data["description"] = []
        if self.config.get("grafana_dev", None):
            data["description"].append(
                "**THIS IS A DEVELOPMENT INSTANCE! It might not work as expected, please use production instance.**"
            )
        else:
            data["description"].append("**THIS IS A PRODUCTION INSTANCE!**")
        data["description"].append(
            "**RTMon (Real-Time Monitoring)** is an automated service within the SENSE project designed to dynamically monitor and visualize network paths provisioned by SENSE Orchestrators. It identifies active service deltas, retrieves path manifests, and generates Grafana dashboards with detailed host, link, and L2 debug views. RTMon integrates with external monitoring systems like ESnet Stardust, Internet2 TSDS, and other domains to normalize metrics across them.\n"
        )
        data["description"].append(
            "It manages lifecycle events by submitting and removing monitoring actions, syncing dashboard state, and triggering diagnostics (e.g., ping) via SiteRM.\n"
        )
        data["description"].append(
            "RTMon loops every 30s, updating visualizations and annotations in real-time, providing end-to-end visibility of cross-domain, intent-driven network services."
        )
        # Add also supported actions
        data["supported_actions"] = list(self.supported_actions.values())
        return data

    def s_getMetadata(self):
        """Get Metadata Information from SENSE-O"""
        dApi = self.s_getMetaApi()
        folderName = self._getFolderName()
        try:
            response = dApi.get_metadata(domain="RTMon", name=folderName)
        except ValueError as ex:
            raise ex
        return response

    def s_registerMetadata(self):
        """Register Metadata Information"""
        dApi = self.s_getMetaApi()
        data = self.s_getMetadataRegData()
        folderName = self._getFolderName()
        try:
            response = dApi.post_metadata(
                data=dumpJson(data, self.logger), domain="RTMon", name=folderName
            )
        except ValueError as ex:
            self.logger.error(f"Metadata raised ValueError for post - {ex}.")
            response = self.s_getMetadata()
        return response

    def s_updateMetadata(self):
        """Check if my instance is the active one."""
        folderName = self._getFolderName()
        myuuid = self._s_getworkeruuid()
        try:
            response = self.s_getMetadata()
        except ValueError as ex:
            self.logger.error(
                f"Metadata raised ValueError - {ex}. No metadata found for {folderName}. Register new one"
            )
            response = self.s_registerMetadata()
        if "uuid" not in response:
            self.logger.error(
                f"Metadata does not have UUID. My UUID is {myuuid}. Failing to run. Response from SENSE-O: {response}"
            )
            raise SENSEOFailure(
                f"Metadata does not have UUID. My UUID is {myuuid}. Failing to run. Response from SENSE-O: {response}"
            )
        if response["uuid"] == myuuid:
            self.s_registerMetadata()
        else:
            # Check if timestamp older than 2 mins (if no entry - force update);
            if getUTCnow() - response.get("last_update", 0) > self.config.get(
                "overtake_time", 120
            ):
                self.logger.error(
                    f"Metadata is older than 2 minutes. Metadata information: UUID: {response}. My UUID is {myuuid}. Last update: {response['last_update']}. Taking over."
                )
                self.s_registerMetadata()
            else:
                raise SENSEOFailure(
                    f"UUID does not match - {response['uuid']} in database. My UUID is {myuuid}. Last update: {response['last_update']}"
                )

    def s_getassignedTasks(self):
        """Get all assigned tasks"""
        tApi = self.s_getTaskApi()
        ret = tApi.get_tasks(assigned="rtmon.instance-manager")
        folderName = self._getFolderName()
        ret = [
            task
            for task in ret
            if task.get("config", {}).get("deployment", "") == folderName
        ]
        return ret

    def _s_gettaskbyuuid(self, taskuuid):
        """Get task by UUID"""
        tasks = self.s_getassignedTasks()
        for task in tasks:
            if task.get("uuid", "") == taskuuid:
                return task
        return None

    def s_setTaskState(self, taskuuid, state, data=None):
        """Set task state"""
        # Get the task from SENSE-O and check if state is different
        if not taskuuid:
            self.logger.error(
                f"No task UUID provided. Ignore to set task state. Data: {data}"
            )
            return None
        task = self._s_gettaskbyuuid(taskuuid)
        if not task:
            return None
        if task.get("status", "") == state:
            return task
        # Check if there are any other changes in reported data;
        tApi = self.s_getTaskApi()
        return tApi.update_task(json.dumps(data), uuid=taskuuid, state=state)

    def s_finishTask(self, taskuuid, data=None):
        """Accept task"""
        if not taskuuid:
            self.logger.error(
                f"No task UUID provided. Ignore to finish task. Data: {data}"
            )
            return None
        task = self._s_gettaskbyuuid(taskuuid)
        if task:
            return self.s_setTaskState(taskuuid, "FINISHED", data)
        return None

    def s_getManifest(self, instance):
        """Create a manifest in SENSE-0"""
        template = {
            "Ports": [
                {
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
                            "sparql": 'SELECT DISTINCT ?host_port ?ipv4 ?ipv6 ?mac WHERE { ?host_vlan_port nml:isAlias ?vlan_port. ?host_port nml:hasBidirectionalPort ?host_vlan_port. OPTIONAL {?host_vlan_port mrs:hasNetworkAddress  ?ipv4na. ?ipv4na mrs:type "ipv4-address". ?ipv4na mrs:value ?ipv4.} OPTIONAL {?host_vlan_port mrs:hasNetworkAddress  ?ipv6na. ?ipv6na mrs:type "ipv6-address". ?ipv6na mrs:value ?ipv6.} OPTIONAL {?host_vlan_port mrs:hasNetworkAddress  ?macana. ?macana mrs:type "mac-address". ?macana mrs:value ?mac.} FILTER NOT EXISTS {?sw_svc mrs:providesSubnet ?vlan_subnt. ?vlan_subnt nml:hasBidirectionalPort ?host_vlan_port.} }',
                            "sparql-ext": 'SELECT DISTINCT ?host_name ?host_port_name  WHERE {?host a nml:Node. ?host nml:hasBidirectionalPort ?host_port. OPTIONAL {?host nml:name ?host_name.} OPTIONAL {?host_port mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type "sense-rtmon:name". ?na_pn mrs:value ?host_port_name.} }',
                            "required": "false",
                        }
                    ],
                    "sparql": "SELECT DISTINCT  ?vlan_port  ?vlan  WHERE { ?subnet a mrs:SwitchingSubnet. ?subnet nml:hasBidirectionalPort ?vlan_port. ?vlan_port nml:hasLabel ?vlan_l. ?vlan_l nml:value ?vlan. }",
                    "sparql-ext": 'SELECT DISTINCT ?terminal ?port_name ?node_name ?peer ?site ?port_mac ?port_ipv4 ?port_ipv6 WHERE { { ?node a nml:Node. ?node nml:name ?node_name. ?node nml:hasBidirectionalPort ?terminal. ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL { ?terminal mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type "sense-rtmon:name". ?na_pn mrs:value ?port_name. } OPTIONAL { ?terminal nml:isAlias ?peer. } OPTIONAL { ?site nml:hasNode ?node. } OPTIONAL { ?site nml:hasTopology ?sub_site. ?sub_site nml:hasNode ?node. } OPTIONAL { ?terminal mrs:hasNetworkAddress ?naportmac. ?naportmac mrs:type "mac-address". ?naportmac mrs:value ?port_mac. } OPTIONAL { ?vlan_port mrs:hasNetworkAddress ?ipv4na. ?ipv4na mrs:type "ipv4-address". ?ipv4na mrs:value ?port_ipv4. } OPTIONAL { ?vlan_port mrs:hasNetworkAddress ?ipv6na. ?ipv6na mrs:type "ipv6-address". ?ipv6na mrs:value ?port_ipv6. } } UNION { ?site a nml:Topology. ?site nml:name ?node_name. ?site nml:hasBidirectionalPort ?terminal. ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL { ?terminal mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type "sense-rtmon:name". ?na_pn mrs:value ?port_name. } OPTIONAL { ?terminal nml:isAlias ?peer. } OPTIONAL { ?terminal mrs:hasNetworkAddress ?naportmac. ?naportmac mrs:type "mac-address". ?naportmac mrs:value ?port_mac. } OPTIONAL { ?vlan_port mrs:hasNetworkAddress ?ipv4na. ?ipv4na mrs:type "ipv4-address". ?ipv4na mrs:value ?port_ipv4. } OPTIONAL { ?vlan_port mrs:hasNetworkAddress ?ipv6na. ?ipv6na mrs:type "ipv6-address". ?ipv6na mrs:value ?port_ipv6. } } }',
                    "required": "true",
                }
            ]
        }
        wApi = self.s_getWorkflowApi()
        wApi.si_uuid = instance["referenceUUID"]
        failures = 0
        response = None
        while failures < 3:
            try:
                response = wApi.manifest_create(dumpJson(template, self.logger))
                failures = 4
            except Exception as ex:
                failures += 1
                self.logger.error(
                    f"Failed to get manifest from SENSE-O for {instance['referenceUUID']}: {ex}"
                )
                time.sleep(5)
        if not response:
            self.logger.error(
                f"Failed to get manifest from SENSE-O for {instance['referenceUUID']} after 3 tries."
            )
            return {}
        json_response = loadJson(response, self.logger)
        if "jsonTemplate" not in json_response:
            self.logger.debug(
                f"WARNING: {instance['referenceUUID']} did not receive correct output!"
            )
            self.logger.debug(f"WARNING: Response: {response}")
            return {}
        manifest = loadJson(json_response["jsonTemplate"], self.logger)
        return manifest

    def s_getInstances(self):
        """Get all instances from SENSE-0"""
        response = None
        try:
            dApi = self.s_getDiscoverApi()
            response = dApi.discover_service_instances_get()
        except Exception as ex:
            self.logger.critical(
                f"API Call Failed!. Exception {ex} Response: {response}"
            )
            raise SENSEOFailure(
                f"API Call Failed!. Exception {ex} Response: {response}"
            ) from ex
        if not response:
            self.logger.error("No Data received from SENSE-O")
            return {}
        # SENSE-O returns str json key - which we need to load and make it a dict
        out = []
        for item in loadJson(response, self.logger).get("instances", []):
            tmpIntents = copy.deepcopy(item["intents"])
            item["intents"] = []
            for intent in tmpIntents:
                if "json" in intent and isinstance(intent["json"], str):
                    intent["json"] = loadJson(intent["json"], self.logger)
                item["intents"].append(intent)
            out.append(item)
        return out

    def s_getInstance(self, instance_uuid):
        """Get instance by UUID"""
        instances = self.s_getInstances()
        for instance in instances:
            if (
                "referenceUUID" in instance
                and instance["referenceUUID"] == instance_uuid
            ):
                return instance
        return {}
