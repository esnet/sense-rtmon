#!/usr/bin/env python3
"""
Class for interacting with SENSE SiteRMs
"""
import time
import random
from RTMonLibs.GeneralLibs import loadJson, getUTCnow, valtoboolean
from sense.client.siterm.debug_api import DebugApi


class SiteRMApi:
    """Class for interacting with SENSE-0 API"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get("config")
        self.logger = kwargs.get("logger")
        self.siterm_debug = DebugApi()

    @staticmethod
    def _sr_all_keys_match(action, newaction, matchkeys=None):
        """Check if all keys in newaction match the action, or only specific keys if matchkeys is provided"""
        if matchkeys:
            return all(action.get(key) == newaction.get(key) for key in matchkeys)
        return all(newaction.get(key) == action.get(key) for key in newaction if key != "runtime")

    def _sr_get_l3_info(self, **kwargs):
        """Get L3 information from instance"""
        out = {}
        try:
            reqtype = kwargs.get("instance", {}).get("intents")[0].get("json", {}).get("data", {}).get("type")
            if reqtype in ["Site-L3 over VLAN-MultiPath", "Site-L3 over P2P VLAN"]:
                for terminal in kwargs["instance"]["intents"][0]["json"]["data"]["connections"][0]["terminals"]:
                    uri = terminal.get("uri", "")
                    iprange = terminal.get("ipv6_prefix_list", {}) if "ipv6_prefix_list" in terminal else terminal.get("ipv4_prefix_list", {})
                    iptype = "ipv6" if "ipv6_prefix_list" in terminal else "ipv4"
                    sitename = self.siterm_debug.getSitename(**{"urn": uri})
                    if sitename and iprange:
                        out.setdefault(sitename, {}).setdefault(iptype, []).append(iprange)
        except Exception as ex:
            self.logger.error(f"Error occurred: {ex}")
        return out

    def _sr_get_all_hosts(self, **kwargs):
        """Get all hosts from manifest"""
        output = {"hosts": [], "switches": [], "ips": {}, "hostips": {}, "switchips": {}, "dynamicranges": {}}
        # Identify from manifest if that is L3 request
        output["dynamicranges"] = self._sr_get_l3_info(**kwargs)

        for _idx, item in enumerate(kwargs.get("manifest", {}).get("Ports", [])):
            # Switch IPs
            for key, defval in [
                ("IPv4", ["?ipv4?", "?port_ipv4?"]),
                ("IPv6", ["?ipv6?", "?port_ipv6?"]),
            ]:
                if item not in output["switches"]:
                    output["switches"].append(item)
                if item.get(key) and item[key] not in defval:
                    output["switchips"].setdefault(key, [])
                    output["switchips"][key].append(item[key].split("/")[0])
                    output["ips"].setdefault(key, [])
                    output["ips"][key].append(item[key].split("/")[0])
            # Host IPs and all Hosts
            for hostdata in item.get("Host", []):
                if item.get("Vlan"):
                    hostdata["vlan"] = f"vlan.{item['Vlan']}"
                if hostdata not in output["hosts"]:
                    output["hosts"].append(hostdata)
                # Check if IPv6 or IPv4 is defined
                for key, defval in [("IPv4", "?ipv4?"), ("IPv6", "?ipv6?")]:
                    if hostdata.get(key) and hostdata[key] not in defval:
                        output["hostips"].setdefault(key, [])
                        output["hostips"][key].append(hostdata[key].split("/")[0])
                        output["ips"].setdefault(key, [])
                        output["ips"][key].append(hostdata[key].split("/")[0])
        return output

    def sr_get_debug_action_info(self, **kwargs):
        """Get debug action info for a specific id"""
        return self.siterm_debug.get_debug(**{"sitename": kwargs.get("sitename"), "id": kwargs.get("id"), "details": kwargs.get("details", True)})

    def sr_get_debug_actions(self, **kwargs):
        """Get all debug actions for a site and hostname"""
        allDebugActions = []
        for key in ["new", "active"]:
            try:
                jsonOut = {}
                out = self.siterm_debug.get_all_debug_hostname(sitename=kwargs.get("sitename"), hostname=kwargs.get("hostname"), state=key, action=kwargs.get("action"))
                allitems = []
                if out and not out[1]:
                    self.logger.error(f"Error getting debug actions for {kwargs.get('sitename')}:{kwargs.get('hostname')} action {kwargs.get('action')}: {out}")
                    continue
                if out and out[0]:
                    allitems = loadJson(out[0], self.logger)
                for tmpitem in allitems:
                    jsonOut = loadJson(tmpitem, self.logger)
                    ditem = self.siterm_debug.get_debug(sitename=kwargs.get("sitename"), id=jsonOut["id"], details=True, state=key)
                    if ditem and not ditem[1]:
                        self.logger.error(f"Error getting debug action info for {kwargs.get('sitename')}:{kwargs.get('hostname')} action {kwargs.get('action')} id {jsonOut['id']}: {ditem}")
                        continue
                    if ditem and ditem[0]:
                        ditem = ditem[0][0]
                        ditem["requestdict"] = loadJson(ditem["requestdict"], self.logger)
                    allDebugActions.append(ditem)
            except Exception as e:
                self.logger.error(f"Failed to get debug actions for {kwargs.get('sitename')}:{kwargs.get('hostname')} action {kwargs.get('action')}: {e}")
                continue
        return allDebugActions

    def _sr_submitsiterm(self, callaction, newaction):
        """Submit action to SiteRM"""
        out = None
        if callaction == "fdt-server":
            out = self.siterm_debug.submit_fdtserver(**newaction)
        elif callaction == "fdt-client":
            out = self.siterm_debug.submit_fdtclient(**newaction)
        elif callaction == "iperf-server":
            out = self.siterm_debug.submit_iperfserver(**newaction)
        elif callaction == "iperf-client":
            out = self.siterm_debug.submit_iperfclient(**newaction)
        elif callaction == "ethr-server":
            out = self.siterm_debug.submit_ethrserver(**newaction)
        elif callaction == "ethr-client":
            out = self.siterm_debug.submit_ethrclient(**newaction)
        elif callaction == "rapid-ping":
            out = self.siterm_debug.submit_ping(**newaction)
        elif callaction == "rapid-pingnet":
            out = self.siterm_debug.submit_pingnet(**newaction)
        else:
            self.logger.error(f"Unknown action {callaction} for {newaction}")
            return None
        if out and not out[1]:
            self.logger.error(f"Error submitting {callaction} test for {newaction}: {out}")
            self.logger.error(f"Error details: {out[2].text}")
            return newaction
        newaction["submit_time"] = getUTCnow()
        newaction["submit_out"] = out[0]
        self.logger.info(f"Submitted {callaction} test for {newaction}: {out}")
        return newaction

    def _sr_submit_pingnet(self, actions, actionsuffix, **kwargs):
        """Submit a host/net ping test to the SENSE-SiteRM API"""
        # There are no parameters for ping test, that we allow to control for users;
        # So there is only one action (and this is already tested that it is enabled)
        actionname = actions[0]
        # In case it is rapidpingnet, then we need to check if test already ran:
        # If already ran, then we do not need to submit again
        # Will need to handle deletion of old tests (uncheckbox)
        # and re-add
        if actionsuffix in kwargs["fout"]:
            self.logger.info(f"{actionsuffix} test already present in output, not submitting again. User should unselect it if they want to resubmit.")
            return None
        self.logger.info(f"Start check for {actionname} test if needed")
        manInfo = self._sr_get_all_hosts(**kwargs)
        ping_out = []
        all_annotations = []
        for host in manInfo.get("switches", []):
            # Check if IPv6 or IPv4 is defined
            for key, defval in [("IPv4", "?ipv4?"), ("IPv6", "?ipv6?")]:
                if host.get(key) and host[key] != defval:
                    hostspl = host.get("Node").split(":")
                    for ip in manInfo.get("ips", {}).get(key, []):
                        hostip = host[key].split("/")[0]
                        if hostip == ip:
                            # We ignore ourself. No need to ping ourself
                            continue
                        # Loop all debug actions and check if the action is already in the list of actions
                        newaction = {
                            "hostname": hostspl[1],
                            "type": actionname,
                            "sitename": hostspl[0],
                            "ip": ip,
                            "timeout": kwargs.get("timeout", 5),
                            "count": kwargs.get("count", 10),
                            "time": kwargs.get("time", 600),
                            "onetime": True,
                        }
                        actionPresent = False
                        allDebugActions = self.sr_get_debug_actions(**{"sitename": hostspl[0], "hostname": hostspl[1], "action": actionname})
                        for action in allDebugActions:
                            if self._sr_all_keys_match(action.get("requestdict"), newaction):
                                actionPresent = True
                                newaction["submit_time"] = action.get("insertdate")
                                newaction["submit_out"] = {"ID": action.get("id"), "Status": action.get("state")}
                                self.logger.info(f"{actionname} test already present for {newaction}: {newaction['submit_out']}")
                                ping_out.append(newaction)
                                break
                        if not actionPresent:
                            self.logger.info(f"Submitting {actionname} test for {newaction}")
                            newaction = self._sr_submitsiterm(actionname, newaction)
                            ping_out.append(newaction)
                            all_annotations.append({"submitout": newaction, "dashbInfo": kwargs["fout"]["dashbInfo"], "timespan": False})
        return ping_out, all_annotations, actionsuffix  # No need annotations for ping (it does not span over time)

    def _sr_findsitermips(self, **kwargs):
        """Find overlapping dynamic ranges"""
        newactions = []
        for sitename, iptypes in kwargs.get("dynamicranges", {}).items():
            for iptype, ipvals in iptypes.items():
                ipval = ipvals[0] if ipvals else None
                out = self.siterm_debug.get_dynamicranges(**{"sitename": sitename})
                if out and not out[1]:
                    self.logger.error(f"Error getting dynamic ranges for {sitename}: {out}")
                    self.logger.error(f"Error details: {out[2].text}")
                    continue
                overlap = False
                for rangeval, values in out[0].get(iptype, {}).items():
                    if rangeval == ipval:
                        overlap = True
                        newactions.append({"iptype": iptype, "dynamicfrom": ipval, "allips": values, "sitename": sitename})
                        break
                # If overlap, we can submit a ping from this site
                if not overlap:
                    self.logger.info(f"No overlapping range found for {sitename} {iptype} {ipval}, cannot submit ping from L3 host")
                    continue
        return newactions

    def _sr_submit_pinghostl3(self, actions, actionsuffix, **kwargs):
        """Submit a Ping from an L3 host to a specific IP"""
        # Implementation for submitting a ping from an L3 host
        # Once we get dynamicfrom, we need to get for each site, if Site has a range
        # that listens on it. If it does, then we submit a new action with host undefined;
        # Also check - should only look for dynamicfrom, ip as overlaping check
        ping_out = []
        all_annotations = []
        actionname = actions[0]
        pingactions = self._sr_findsitermips(**kwargs)
        if not pingactions or len(pingactions) != 2:
            self.logger.info("No overlapping ranges found for both Sites IPs, cannot submit ping from L3 host")
        for indx, item in enumerate(pingactions):
            remsiteid = 1 if indx == 0 else 0
            self.logger.info(f"Found overlapping range for {item['sitename']} {item['iptype']} {item['dynamicfrom']}, can submit ping from L3 host")
            # We have a range that overlaps, we can submit a ping from this site
            newaction = {
                "type": actionname,
                "sitename": item["sitename"],
                "dynamicfrom": item["dynamicfrom"],
                "ip": random.choice(pingactions[remsiteid]["allips"]),
                "timeout": kwargs.get("timeout", 5),
                "count": kwargs.get("count", 10),
                "time": kwargs.get("time", 600),
                "onetime": True,
            }
            actionPresent = False
            allDebugActions = self.sr_get_debug_actions(**{"sitename": item["sitename"], "action": actionname})
            for action in allDebugActions:
                # debug needs to check everything, execpt hostname. Hostname is undefined and that is changed by RM;
                if self._sr_all_keys_match(action.get("requestdict"), newaction, ["type", "sitename", "dynamicfrom", "ip", "timeout", "count", "time", "onetime"]):
                    actionPresent = True
                    newaction["submit_time"] = action.get("insertdate")
                    newaction["submit_out"] = {"ID": action.get("id"), "Status": action.get("state")}
                    self.logger.info(f"{actionname} test already present for {newaction}: {newaction['submit_out']}")
                    ping_out.append(newaction)
                    break
            if not actionPresent:
                self.logger.info(f"Submitting {actionname} test for {newaction}")
                newaction = self._sr_submitsiterm(actionname, newaction)
                ping_out.append(newaction)
                all_annotations.append({"submitout": newaction, "dashbInfo": kwargs["fout"]["dashbInfo"], "timespan": False})
        return ping_out, all_annotations, actionsuffix
        # Call and get all ranges at the site

    def _sr_submit_pinghost(self, actions, actionsuffix, **kwargs):
        """Submit a host/net ping test to the SENSE-SiteRM API"""
        # There are no parameters for ping test, that we allow to control for users;
        # So there is only one action (and this is already tested that it is enabled)
        actionname = actions[0]
        self.logger.info(f"Start check for {actionname} test if needed")
        manInfo = self._sr_get_all_hosts(**kwargs)
        ping_out = []
        all_annotations = []
        # Submit L3 hosts pings, if dynamic ranges are defined
        if manInfo.get("dynamicranges", {}):
            kwargs["dynamicranges"] = manInfo.get("dynamicranges", {})
            self.logger.info(f"Submitting {actionname} test from L3 hosts")
            return self._sr_submit_pinghostl3(actions, actionsuffix, **kwargs)
        # Otherwise, do a L2 host pings
        for host in manInfo.get("hosts", []):
            # Check if IPv6 or IPv4 is defined
            for key, defval in [("IPv4", "?ipv4?"), ("IPv6", "?ipv6?")]:
                if host.get(key) and host[key] != defval:
                    hostspl = host.get("Name").split(":")
                    for ip in manInfo.get("ips", {}).get(key, []):
                        hostip = host[key].split("/")[0]
                        if hostip == ip:
                            # We ignore ourself. No need to ping ourself
                            continue
                        # Loop all debug actions and check if the action is already in the list of actions
                        newaction = {
                            "hostname": hostspl[1],
                            "type": actionname,
                            "sitename": hostspl[0],
                            "ip": ip,
                            "packetsize": kwargs.get("packetsize", 56),
                            "interval": kwargs.get("interval", 5),
                            "interface": host["Interface"] if not host.get("vlan") else host["vlan"],
                            "time": kwargs.get("time", 600),
                            "onetime": False,
                        }
                        actionPresent = False
                        allDebugActions = self.sr_get_debug_actions(**{"sitename": hostspl[0], "hostname": hostspl[1], "action": actionname})
                        for action in allDebugActions:
                            if self._sr_all_keys_match(action.get("requestdict"), newaction):
                                actionPresent = True
                                newaction["submit_time"] = action.get("insertdate")
                                newaction["submit_out"] = {"ID": action.get("id"), "Status": action.get("state")}
                                self.logger.info(f"{actionname} test already present for {newaction}: {newaction['submit_out']}")
                                ping_out.append(newaction)
                                break
                        if not actionPresent:
                            self.logger.info(f"Submitting {actionname} test for {newaction}")
                            newaction = self._sr_submitsiterm(actionname, newaction)
                            ping_out.append(newaction)
                            all_annotations.append({"submitout": newaction, "dashbInfo": kwargs["fout"]["dashbInfo"], "timespan": False})
        return ping_out, all_annotations, actionsuffix

    def _sr_wait_active(self, sitename, actionid, maxtime=120):
        """Wait for an action to become active"""
        if not actionid:
            self.logger.error("No action ID provided to wait for active check/wait")
            return None
        starttime = getUTCnow()
        lastitem = None
        while (getUTCnow() - starttime) < maxtime:
            lastitem = self.sr_get_debug_action_info(**{"sitename": sitename, "id": actionid})
            status = lastitem[0][0]["state"] if lastitem and lastitem[0] and lastitem[0][0] and "state" in lastitem[0][0] else "unknown"
            if status == "active":
                self.logger.info(f"Action {actionid} is now active")
                return lastitem
            time.sleep(5)
        self.logger.warning(f"Action {actionid} did not become active within {maxtime} seconds")
        return lastitem

    def _sr_submit_transferl3(self, actions, actionsuffix, **kwargs):
        """Submit an fdt test from an L3 host to another L3 host"""

        # Implementation for submitting an fdt test from an L3 host to another L3 host
        def _getportip(item):
            return item.get("port"), item.get("selectedip")

        submitout = []
        all_annotations = []
        actionname = actions[0]
        transferactions = self._sr_findsitermips(**kwargs)
        if not transferactions or len(transferactions) != 2:
            self.logger.info(f"No overlapping ranges found for both Sites IPs, cannot submit {actionname} from L3 host")
            return None
        # Identify servers and clients where to run
        # If both directions are defined, then we need to check both directions
        serverlist, clientlist, serverports, serverips = [], [], [], []
        if kwargs["transferparams"]["bothdirections"]:
            self.logger.info("Both directions are defined, checking both")
            serverlist = [transferactions[0], transferactions[1]]
            clientlist = [transferactions[1], transferactions[0]]
        else:
            self.logger.info("Only one direction is defined, checking one")
            serverlist = [transferactions[0]]
            clientlist = [transferactions[1]]

        for callaction, hostlist in [(actions[0], serverlist), (actions[1], clientlist)]:
            for itemid, item in enumerate(hostlist):
                newaction = {"hostname": "undefined", "type": callaction, "sitename": item["sitename"], "dynamicfrom": item["dynamicfrom"], "time": max(kwargs["transferparams"]["runtime"], 660)}
                # If action is client, then we need to add streams
                if callaction.endswith("client"):
                    newaction["streams"] = kwargs["transferparams"]["streams"]
                    # If port is not available, then something failed, we try to submit, but that
                    # gonna fail. This is just to prevent continuous resubmission of the same test
                    newaction["ip"] = serverips[itemid] if itemid < len(serverips) else None
                    newaction["port"] = serverports[itemid] if itemid < len(serverports) else None
                    if not newaction["port"] or not newaction["ip"]:
                        self.logger.error(f"Port for {newaction} is not available, cannot submit client test")
                        continue
                actionPresent = False
                # Loop all debug actions and check if the action is already in the list of actions
                allDebugActions = self.sr_get_debug_actions(**{"sitename": item["sitename"], "action": callaction})
                for findactions in allDebugActions:
                    tmpcheckkeys = ["type", "sitename", "dynamicfrom", "time"]
                    if callaction.endswith("client"):
                        tmpcheckkeys.extend(["streams", "ip", "port"])
                    if self._sr_all_keys_match(findactions.get("requestdict"), newaction, tmpcheckkeys):
                        actionPresent = True
                        newaction["submit_time"] = findactions.get("insertdate")
                        newaction["submit_out"] = {"ID": findactions.get("id"), "Status": findactions.get("state")}
                        self.logger.info(f"{callaction} test already present for {newaction}: {newaction['submit_out']}")
                        submitout.append(newaction)
                        # need to get port and server ip if server
                        if callaction.endswith("server"):
                            portip = _getportip(findactions.get("requestdict"))
                            serverports.append(portip[0])
                            serverips.append(portip[1])
                        break
                if not actionPresent:
                    self.logger.info(f"Submitting {callaction} test for {newaction}")
                    out = self._sr_submitsiterm(callaction, newaction)
                    # Submit annotation should be done if return code is OK and there is an ID
                    # Also we need to get back the submitted information, so that we know the port (if that is server)
                    if out and out.get("submit_out", {}).get("ID") and callaction.endswith("server"):
                        dbout = self.sr_get_debug_action_info(sitename=item["sitename"], id=out["submit_out"]["ID"])
                        # Lets find out the port number
                        if dbout and dbout[0] and dbout[0][0] and dbout[0][0].get("requestdict"):
                            dbout[0][0]["requestdict"] = loadJson(dbout[0][0]["requestdict"], self.logger)
                            # Now we can submit annotation
                        all_annotations.append({"submitout": out, "dashbInfo": kwargs["fout"]["dashbInfo"], "storeresults": [item["sitename"], "undefined", callaction]})
                    submitout.append(out)
                    # If the action is a server action, we need to wait for it to become active
                    if callaction.endswith("server"):
                        lastitem = self._sr_wait_active(item["sitename"], out.get("submit_out", {}).get("ID"))
                        if lastitem and lastitem[0] and lastitem[0][0] and lastitem[0][0].get("requestdict"):
                            lastitem[0][0]["requestdict"] = loadJson(lastitem[0][0]["requestdict"], self.logger)
                            portip = _getportip(lastitem[0][0]["requestdict"])
                            serverports.append(portip[0])
                            serverips.append(portip[1])
        return submitout, all_annotations, actionsuffix

    def _sr_submit_transfer(self, actions, actionsuffix, **kwargs):
        """Submit an fdt test to the SENSE-SiteRM API"""
        # If already ran, then we do not need to submit again
        # Will need to handle deletion of old tests (uncheckbox)
        # and re-add
        if actionsuffix in kwargs["fout"]:
            self.logger.info(f"{actionsuffix} test already present in output, not submitting again. User should unselect it if they want to resubmit.")
            return None
        self.logger.info(f"Start check for {actionsuffix} test if needed")
        manInfo = self._sr_get_all_hosts(**kwargs)
        # based on our variables;
        submitout = []
        if len(manInfo.get("hosts", [])) < 2 and not manInfo.get("dynamicranges", {}):
            self.logger.info(f"Not enough hosts to submit {actionsuffix} test")
            return None
        if manInfo.get("dynamicranges", {}):
            kwargs["dynamicranges"] = manInfo.get("dynamicranges", {})
            self.logger.info(f"Submitting {actionsuffix} test from L3 hosts")
            return self._sr_submit_transferl3(actions, actionsuffix, **kwargs)
        # If both directions are defined, then we need to check both directions
        serverlist, clientlist, serverports = [], [], []
        if kwargs["transferparams"]["bothdirections"]:
            self.logger.info("Both directions are defined, checking both")
            serverlist = [manInfo["hosts"][0], manInfo["hosts"][1]]
            clientlist = [manInfo["hosts"][1], manInfo["hosts"][0]]
        else:
            self.logger.info("Only one direction is defined, checking one")
            serverlist = [manInfo["hosts"][0]]
            clientlist = [manInfo["hosts"][1]]
        all_annotations = []
        for callaction, hostlist in [(actions[0], serverlist), (actions[1], clientlist)]:
            for itemid, host in enumerate(hostlist):
                # Check if IPv6 or IPv4 is defined
                for key, defval in [("IPv4", "?ipv4?"), ("IPv6", "?ipv6?")]:
                    if host.get(key) and host[key] != defval:
                        hostspl = host.get("Name").split(":")
                        totaltime = kwargs["transferparams"]["runtime"]
                        totaltime = 660 if totaltime < 660 else totaltime  # Give it 1 min headroom to start
                        newaction = {"hostname": hostspl[1], "type": callaction, "sitename": hostspl[0], "ip": host[key].split("/")[0], "time": totaltime}
                        # If action is client, then we need to add streams
                        if callaction.endswith("client"):
                            # Need to tell the correct IP
                            newaction["ip"] = manInfo["hosts"][1][key].split("/")[0] if host == manInfo["hosts"][0] else manInfo["hosts"][0][key].split("/")[0]
                            newaction["streams"] = kwargs["transferparams"]["streams"]
                            # If port is not available, then something failed, we try to submit, but that
                            # gonna fail. This is just to prevent continuous resubmission of the same test
                            newaction["port"] = serverports[itemid] if itemid < len(serverports) else None
                            if not newaction["port"]:
                                self.logger.error(f"Port for {newaction} is not available, cannot submit client test")
                                continue
                        actionPresent = False
                        # Loop all debug actions and check if the action is already in the list of actions
                        allDebugActions = self.sr_get_debug_actions(**{"sitename": hostspl[0], "hostname": hostspl[1], "action": callaction})
                        for findactions in allDebugActions:
                            if self._sr_all_keys_match(findactions.get("requestdict"), newaction):
                                actionPresent = True
                                newaction["submit_time"] = findactions.get("insertdate")
                                newaction["submit_out"] = {"ID": findactions.get("id"), "Status": findactions.get("state")}
                                self.logger.info(f"{callaction} test already present for {newaction}: {newaction['submit_out']}")
                                submitout.append(newaction)
                                break
                        if not actionPresent:
                            self.logger.info(f"Submitting {callaction} test for {newaction}")
                            out = self._sr_submitsiterm(callaction, newaction)
                            # Submit annotation should be done if return code is OK and there is an ID
                            # Also we need to get back the submitted information, so that we know the port (if that is server)
                            if out and out.get("submit_out", {}).get("ID") and callaction.endswith("server"):
                                dbout = self.sr_get_debug_action_info(sitename=hostspl[0], id=out["submit_out"]["ID"])
                                # Lets find out the port number
                                if dbout and dbout[0] and dbout[0][0] and dbout[0][0].get("requestdict"):
                                    dbout[0][0]["requestdict"] = loadJson(dbout[0][0]["requestdict"], self.logger)
                                    serverports.append(dbout[0][0]["requestdict"].get("port"))
                                    # Now we can submit annotation
                                all_annotations.append({"submitout": out, "dashbInfo": kwargs["fout"]["dashbInfo"], "storeresults": [hostspl[0], hostspl[1], callaction]})
                            submitout.append(out)
                            # If the action is a server action, we need to wait for it to become active
                            if callaction.endswith("server"):
                                self._sr_wait_active(hostspl[0], out["submit_out"]["ID"])
        return submitout, all_annotations, actionsuffix

    def sr_submit_fdt(self, **kwargs):
        """Submit an fdt test to the SENSE-SiteRM API"""
        return self._sr_submit_transfer(["fdt-server", "fdt-client"], "fdt", **kwargs)

    def sr_submit_iperf(self, **kwargs):
        """Submit an iperf test to the SENSE-SiteRM API"""
        return self._sr_submit_transfer(["iperf-server", "iperf-client"], "iperf", **kwargs)

    def sr_submit_ethr(self, **kwargs):
        """Submit an ethr test to the SENSE-SiteRM API"""
        return self._sr_submit_transfer(["ethr-server", "ethr-client"], "ethr", **kwargs)

    def sr_submit_pinghost(self, **kwargs):
        """Submit a ping test to the SENSE-SiteRM API (for hosts)"""
        return self._sr_submit_pinghost(["rapid-ping"], "pinghost", **kwargs)

    def sr_submit_pingnet(self, **kwargs):
        """Submit a ping test to the SENSE-SiteRM API (for network endpoints)"""
        return self._sr_submit_pingnet(["rapid-pingnet"], "pingnet", **kwargs)

    def sr_submit_perf(self, **kwargs):
        """Submit a performance test to the SENSE-SiteRM API"""
        reqsettings = kwargs["fout"]["taskinfo"]["config"]["settings"]
        #'executeperf.perfapp': 'iperf'
        perfapp = reqsettings.get("executeperf.perfapp", "notselected")
        method = getattr(self, f"sr_submit_{perfapp}", None)
        if callable(method):
            conf = {
                "streams": int(reqsettings.get("executeperf.streams", 4)),
                "bothdirections": valtoboolean(reqsettings.get("executeperf.bothdirections", False)),
                "runtime": int(reqsettings.get("executeperf.runtime", 600)),
            }
            kwargs["transferparams"] = conf
            return method(**kwargs)
        self.logger.error(f"Unknown performance app {perfapp}")
        return None

    def sr_submit_action(self, action, fout, **kwargs):
        """Submit a debug action to the SENSE-SiteRM API"""
        method = getattr(self, f"sr_submit_{action[7:]}", None)
        if callable(method):
            kwargs["fout"] = fout
            kwargs["action"] = action
            tmpOut = method(**kwargs)
            return tmpOut
        return None

    def sr_cancel_action(self, action, fout, **kwargs):
        """Cancel all actions of a specific type"""

        def pruneEmpty(d, keys):
            """Recursively delete nested keys, pruning empty dicts."""
            if not keys:
                return
            k = keys[0]
            if k not in d:
                return
            if len(keys) == 1:
                d.pop(k, None)
            else:
                pruneEmpty(d[k], keys[1:])
                if not d[k]:
                    d.pop(k, None)

        for item in fout.get(action, []):
            if item.get("submit_out", {}).get("ID"):
                # Get item information;
                cancelpossible = True
                dbinfo = self.sr_get_debug_action_info(sitename=item["sitename"], id=item["submit_out"]["ID"], details=False)
                if not dbinfo or not dbinfo[0] or not dbinfo[0][0]:
                    self.logger.warning(f"Cannot get info for {item}, cannot cancel")
                    cancelpossible = False
                if cancelpossible:
                    dbinfo = dbinfo[0][0]
                    # And based on info received, if it is in new or active state, we can cancel it
                    if dbinfo.get("state") not in ["new", "active", "failed"]:
                        self.logger.warning(f"Cannot cancel {item}, state is {dbinfo.get('state')}")
                        cancelpossible = False
                if cancelpossible:
                    updateentry = {"id": item["submit_out"]["ID"], "sitename": item["sitename"], "state": "cancel"}
                    out = self.siterm_debug.update_debug(**updateentry)
                    self.logger.info(f"Cancelled {action} test for {item}: {out}")
                # Need to look at all annotations for this host/action and if it is not a ping
                # we need to update the time_to to be the current time.
                # Also, only do this, if this is renew, in case delete, the dashboard is gone anyway
                if kwargs.get("callstate") == "renew" and fout.get("all_annotations", {}).get(action, {}).get(item["sitename"], {}).get(item.get("hostname", "undefined"), {}).get(item["type"], []):
                    try:
                        self.g_updateAnnotationEndTime(annotation_ids=fout["all_annotations"][action][item["sitename"]][item.get("hostname", "undefined")][item["type"]], time_to=getUTCnow() * 1000)
                    except Exception as e:
                        self.logger.error(f"Error updating annotation end time for {item}: {e}")
                    pruneEmpty(fout["all_annotations"], [action, item["sitename"], item["hostname"], item["type"]])
        return fout
