#!/usr/bin/env python3
"""
Class for interacting with SENSE SiteRMs
"""
import time
from RTMonLibs.GeneralLibs import loadJson
from sense.client.siterm.debug_api import DebugApi


class SiteRMApi:
    """Class for interacting with SENSE-0 API"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get("config")
        self.logger = kwargs.get("logger")
        self.siterm_debug = DebugApi()

    @staticmethod
    def _sr_all_keys_match(action, newaction):
        return all(newaction.get(key) == action.get(key) for key in newaction)

    def _sr_get_all_hosts(self, **kwargs):
        """Get all hosts from manifest"""
        allHosts, allIPs = [], {}
        for _idx, item in enumerate(kwargs.get("manifest", {}).get("Ports", [])):
            # Switch IPs
            for key, defval in [
                ("IPv4", ["?ipv4?", "?port_ipv4?"]),
                ("IPv6", ["?ipv6?", "?port_ipv6?"]),
            ]:
                if item.get(key) and item[key] not in defval:
                    allIPs.setdefault(key, [])
                    allIPs[key].append(item[key].split("/")[0])
            # Host IPs and all Hosts
            for hostdata in item.get("Host", []):
                if item.get("Vlan"):
                    hostdata["vlan"] = f"vlan.{item['Vlan']}"
                allHosts.append(hostdata)
                # Check if IPv6 or IPv4 is defined
                for key, defval in [("IPv4", "?ipv4?"), ("IPv6", "?ipv6?")]:
                    if hostdata.get(key) and hostdata[key] not in defval:
                        allIPs.setdefault(key, [])
                        allIPs[key].append(hostdata[key].split("/")[0])
        return allHosts, allIPs

    def sr_get_debug_actions(self, **kwargs):
        """Get all debug actions for a site and hostname"""
        allDebugActions = []
        for key in ["new", "active"]:
            jsonOut = {}
            out = self.siterm_debug.get_all_debug_hostname(
                sitename=kwargs.get("sitename"),
                hostname=kwargs.get("hostname"),
                state=key,
            )
            allitems = []
            if out and out[0]:
                allitems = loadJson(out[0], self.logger)
            for tmpitem in allitems:
                jsonOut = loadJson(tmpitem, self.logger)
                ditem = self.siterm_debug.get_debug(
                    sitename=kwargs.get("sitename"), id=jsonOut["id"]
                )
                if ditem and ditem[0]:
                    ditem = ditem[0]
                    ditem["requestdict"] = loadJson(ditem["requestdict"], self.logger)
                allDebugActions.append(ditem)
        return allDebugActions

    def sr_submit_ping(self, **kwargs):
        """Submit a ping test to the SENSE-SiteRM API"""
        self.logger.info("Start check for ping test if needed")
        hosts, allIPs = self._sr_get_all_hosts(**kwargs)
        # based on our variables;
        ping_out = []
        for host in hosts:
            # Check if IPv6 or IPv4 is defined
            for key, defval in [("IPv4", "?ipv4?"), ("IPv6", "?ipv6?")]:
                if host.get(key) and host[key] != defval:
                    hostspl = host.get("Name").split(":")
                    try:
                        allDebugActions = self.sr_get_debug_actions(
                            **{"sitename": hostspl[0], "hostname": hostspl[1]}
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to get debug actions for {hostspl[0]}:{hostspl[1]}: {e}"
                        )
                        allDebugActions = []
                        continue
                    for ip in allIPs.get(key, []):
                        hostip = host[key].split("/")[0]
                        if hostip == ip:
                            # We ignore ourself. No need to ping ourself
                            continue
                        # Loop all debug actions and check if the action is already in the list of actions
                        newaction = {
                            "hostname": hostspl[1],
                            "type": "rapid-ping",
                            "sitename": hostspl[0],
                            "ip": ip,
                            "packetsize": kwargs.get("packetsize", 56),
                            "interval": kwargs.get("interval", 5),
                            "interface": host["Interface"]
                            if not host.get("vlan")
                            else host["vlan"],
                            "time": kwargs.get("time", 1800),
                            "onetime": False,
                        }
                        actionPresent = False
                        for action in allDebugActions:
                            if self._sr_all_keys_match(
                                action.get("requestdict"), newaction
                            ):
                                actionPresent = True
                                break
                        if not actionPresent:
                            self.logger.info(f"Submitting ping test for {newaction}")
                            out = self.siterm_debug.submit_ping(**newaction)
                            newaction["submit_time"] = int(time.time())
                            newaction["submit_out"] = out[0]
                            self.logger.info(
                                f"Submitted ping test for {newaction}: {out}"
                            )
                            ping_out.append(newaction)
        return ping_out
