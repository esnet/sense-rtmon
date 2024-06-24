#!/usr/bin/env python3
"""
Class for overriding site specific settings (e.g. OpenNSA/NSI/NRM Name, ports)
"""
from RTMonLibs.GeneralLibs import loadYaml, getWebContentFromURL

class SiteOverride:
    """Site Override"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        self.override = {}
        self._getOverrides()
        self.peers = {}

    def _getOverrides(self):
        """Get all overrides from a config file"""
        if not self.config.get('override_url'):
            self.logger.error("No override URL set for parsing/mapping peers")
            return
        tmpoverrides = getWebContentFromURL(self.config['override_url'], self.logger)
        if tmpoverrides:
            self.override = loadYaml(tmpoverrides.text, self.logger)
        else:
            self.logger.error("Failed to get overrides from URL: %s", self.config['override_url'])

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
        nname = ""
        for item in tmpPort:
            if item != "+":
                if nname:
                    nname = f"{nname}|{item}"
                else:
                    nname = item
        return sitename, nname

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
