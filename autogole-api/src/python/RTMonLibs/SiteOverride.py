#!/usr/bin/env python3
"""
Class for overriding site specific settings (e.g. OpenNSA/NSI/NRM Name, ports)
"""
class SiteOverride:
    """Site Override"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        # TODO: To load automatically config
        self.override = {"urn:ogf:network:icair.org:2013": {"name": "NSI_STARLIGHT", "joint_net": False},
                         "urn:ogf:network:es.net:2013": {"name": "ESNET", "joint_net": True},
                         "urn:ogf:network:stack-fabric:2024": {"name": "NSI_FABRIC", "joint_net": True},
                         "urn:ogf:network:lsanca.pacificwave.net:2016": {"name": "NSI_PACWAVE", "joint_net": False}}
        self.peers = {} # Get all peers mapping from input config


    def so_mappeers(self, indata):
        """Map all peers"""
        self.peers = {}
        for item in indata["Ports"]:
            if item["Peer"] != "?peer?":
                self.peers[item["Port"]] = item["Peer"]
                self.peers[item["Peer"]] = item["Port"]
            if item.get('Host', []):
                for hostdata in item['Host']:
                    self.peers[hostdata['Name']] = item["Port"]
                    self.peers[item["Port"]] = hostdata['Name']


    def _so_getpeer(self, indata, _override):
        """Get peer"""
        if indata["Peer"] != "?peer?":
            return indata["Peer"]
        if indata["Port"] in self.peers:
            return self.peers[indata["Port"]]
        return "?peer?"

    def _so_getname(self, indata, _override):
        """Get name"""
        splPort = indata["Port"].split(":")
        if splPort[-1] != "+":
            return splPort[-1]
        return splPort[-2]

    def _so_getnode(self, indata, override):
        """Get node"""
        sitename = self.override[override]["name"]
        # Cut out override from port
        tmpPort = indata["Port"].replace(override, '').strip(':')
        return f"{sitename}:{tmpPort.split(':')[0]}"
        #return f"{sitename}:{tmpPort}"

    def _so_getjointname(self, indata, override):
        """Get joint name"""
        sitename = self.override[override]["name"]
        tmpPort = indata["Port"].replace(override, '').strip(':').split(':')
        return sitename, f"{tmpPort[0]}_{tmpPort[1]}"

    def so_override(self, indata):
        """Override site specific settings"""
        for override, vals in self.override.items():
            if indata.get("Port", "").startswith(override):
                self.logger.info(f"Overriding site specific settings for {override}")
                # override Node
                indata["Node"] = self._so_getnode(indata, override)
                # override Name
                indata["Name"] = self._so_getname(indata, override)
                # override Peer - if not available
                indata["Peer"] = self._so_getpeer(indata, override)
                if vals.get("joint_net", False):
                    indata['JointSite'], indata["JointNetwork"] = self._so_getjointname(indata, override)
        return indata
