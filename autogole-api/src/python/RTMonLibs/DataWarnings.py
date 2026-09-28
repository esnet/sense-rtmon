#!/usr/bin/env python3
# pylint: disable=E1101,line-too-long
"""Graph generation warnings and monitoring data availability (issue #204).

A panel with no data behind it draws a flat line, which reads as a dead transfer
rather than as missing monitoring. These checks drop such panels and record why.

Verdicts are tri-state: True, False, and None for "could not tell". Only a
definitive False hides anything, so a Prometheus outage never blanks a dashboard.

This applies to Prometheus-backed devices only. ESnet panels are fed by Stardust,
where interfaces are known to appear with a delay, so ESnet is never gated here.
"""
from html import escape as escapeHTML
from RTMonLibs.GeneralLibs import _processName


class DataWarnings:
    """Collects graph generation warnings and gates panels on data availability."""

    @staticmethod
    def t_prometheusBacked(sitehost):
        """True if this device's panels come from Prometheus rather than Stardust."""
        return sitehost.split(":")[0].lower() != "esnet"

    def t_recordWarning(self, msg):
        """Record an issue for the summary row at the bottom of the dashboard."""
        if msg not in self.datawarnings:
            self.logger.info(f"Graph generation warning: {msg}")
            self.datawarnings.append(msg)

    def t_recordAvailability(self, dtype, sitehost, available):
        """Cache an availability verdict and describe it in the summary row."""
        self.dataavailable[(dtype, sitehost)] = available
        if available is True:
            return available
        what = "SNMP" if dtype == "Switch" else "host monitoring"
        if available is None:
            self.t_recordWarning(f"Could not determine whether {what} data exists for {dtype.lower()} {sitehost}. Prometheus did not answer the check, so panels are left in place.")
        elif self.debugmode:
            self.t_recordWarning(f"No {what} data in Prometheus for {dtype.lower()} {sitehost}. Panels are shown anyway because debugmode is enabled, and they are expected to be empty.")
        else:
            self.t_recordWarning(f"No {what} data in Prometheus for {dtype.lower()} {sitehost}. Its flow and L2 debugging panels are not shown.")
        return available

    def t_dataAvailable(self, dtype, sitehost, sitename, hostname):
        """Tri-state check of whether monitoring data backs this device.

        Cached, because the flow panels and the L2 debugging row need the same
        answer and there is no reason to ask Prometheus twice.
        """
        if not self.t_prometheusBacked(sitehost):
            return None
        key = (dtype, sitehost)
        if key in self.dataavailable:
            return self.dataavailable[key]
        if dtype == "Switch":
            available = self.p_get_switch_template_state(sitename=sitename, hostname=hostname)[1]
        else:
            available = self.p_check_host_available(sitename=sitename, hostname=hostname)
        return self.t_recordAvailability(dtype, sitehost, available)

    def t_qosAvailable(self, sitehost, sitename, hostname, vlans):
        """Tri-state check of whether SENSE QoS reservation data backs this switch.

        Kept apart from t_dataAvailable because the two answer different
        questions: SNMP counters and QoS reservations come from different parts
        of SNMPMon, and a switch that reports interface statistics may report no
        reservation at all. Gating the QoS panel on the SNMP answer would show an
        empty panel on exactly the switches that have no reservation to show.
        """
        if not self.t_prometheusBacked(sitehost):
            return None
        available = self.p_check_qos_available(sitename=sitename, hostname=hostname, vlans=vlans)
        if available is True:
            return available
        if available is None:
            self.t_recordWarning(f"Could not determine whether QoS reservation data exists for switch {sitehost}. Prometheus did not answer the check, so the panel is left in place.")
        elif self.debugmode:
            self.t_recordWarning(f"No QoS reservation data in Prometheus for switch {sitehost}. The panel is shown anyway because debugmode is enabled, and it is expected to be empty.")
        else:
            self.t_recordWarning(f"No QoS reservation data in Prometheus for switch {sitehost}. Its QoS panel is not shown.")
        return available

    def t_bgpAvailable(self, sitehost, sitename, hostname):
        """Tri-state check of whether BGP session data backs this switch.

        The bgp_session_state metric is exported by the SiteRM FE and scraped
        by Prometheus, so for Prometheus-backed switches this asks the same
        question the BGP panel itself would. Kept apart from t_dataAvailable
        because a switch that reports SNMP counters may report no BGP sessions.
        """
        if not self.t_prometheusBacked(sitehost):
            return None
        available = self.p_check_bgp_available(sitename=sitename, hostname=hostname)
        if available is True:
            return available
        if available is None:
            self.t_recordWarning(f"Could not determine whether BGP session data exists for switch {sitehost}. Prometheus did not answer the check, so the panel is left in place.")
        elif self.debugmode:
            self.t_recordWarning(f"No BGP session data in Prometheus for switch {sitehost}. The panel is shown anyway because debugmode is enabled, and it is expected to be empty.")
        else:
            self.t_recordWarning(f"No BGP session data in Prometheus for switch {sitehost}. Its BGP panel is not shown.")
        return available

    # Mermaid styling for a switch that has not learned the far end of the path
    # (issue #208). Applied as a separate class statement rather than by
    # decorating the node lines, because the verdict is only known after the
    # whole graph has been walked and every MAC recorded.
    macMissingClass = "rtmonMacMissing"
    macMissingStyle = f"classDef {macMissingClass} fill:#ffeeee,stroke:#cc0000,stroke-width:2px;"

    def t_macLearningMissing(self, sitehost, sitename, hostname):
        """MACs this switch should have learned but definitively has not.

        Asks exactly what the L2 debugging panel graphs, one query per VLAN and
        far end, and returns the ones that came back zero. A None anywhere is
        left out: an unanswered Prometheus must not paint a working switch red.

        Gated on the device reporting a mac table in the first place. Almost
        none do, so without that gate every switch on every path would come back
        as having lost the far end, and the colour would mean nothing.

        Reports a partial failure, not only a total one. A switch that learned
        one end of the path and not the other is the case worth finding, and
        requiring every MAC to be missing would hide it.
        """
        missing = []
        if not self.t_prometheusBacked(sitehost):
            return missing
        if self.p_check_mac_table_available(sitename=sitename, hostname=hostname) is not True:
            # No table, or Prometheus did not say. Either way there is nothing
            # here to call missing. Only worth a line when debugging, since this
            # is the normal case rather than a fault.
            if self.debugmode:
                self.t_recordWarning(f"Switch {sitehost} reports no MAC table to Prometheus, so its MAC learning is not checked in the flow diagram.")
            return missing
        vlans = []
        for intfdata in self.m_groups["Switches"].get(sitehost, {}).values():
            vlan = intfdata.get("Vlan") if isinstance(intfdata, dict) else None
            if vlan and str(vlan) not in vlans:
                vlans.append(str(vlan))
        for vlan in vlans:
            for ssite, sdata in self.mac_addresses.items():
                for mhost, macaddr in sdata.items():
                    if not macaddr or sitehost == ssite:
                        continue
                    learned = self.p_check_mac_learned(sitename=sitename, hostname=hostname, macaddress=macaddr, vlan=vlan)
                    if learned is False:
                        missing.append((f"{ssite} {mhost}", macaddr, vlan))
        return missing

    def t_macLearningStyles(self):
        """Mermaid class statements colouring switches that lost the far end.

        Returns the lines to append to the graph, and records a warning naming
        each device and MAC, so the summary row says which hop to look at rather
        than only that the picture has red in it.
        """
        nodes = []
        for sitehost in self.m_groups["Switches"]:
            parts = sitehost.split(":")
            if len(parts) != 2:
                # No site:device split, so there is nothing to query Prometheus
                # with. _t_addSwitchL2Debugging hits the same case and says so.
                continue
            if self.t_skipMonitoring("Switch", sitehost):
                # Already dropped from the dashboard for having no SNMP data at
                # all. Colouring it for a missing MAC would name a second cause
                # for one fault.
                continue
            missing = self.t_macLearningMissing(sitehost, parts[0], parts[1])
            if not missing:
                continue
            for far, macaddr, vlan in missing:
                self.t_recordWarning(f"Switch {sitehost} has not learned the MAC {macaddr} of {far} on VLAN {vlan}. It is marked in red in the flow diagram.")
            for name in self.m_groups["Switches"].get(sitehost, {}):
                node = _processName(f"{sitehost}_{name}")
                if node not in nodes:
                    nodes.append(node)
        if not nodes:
            return []
        return [self.macMissingStyle, f"class {','.join(nodes)} {self.macMissingClass};"]

    def t_skipMonitoring(self, dtype, sitehost):
        """Decide whether to leave this device out of the dashboard."""
        if self.debugmode or not self.t_prometheusBacked(sitehost):
            return False
        key = (dtype, sitehost)
        if key not in self.dataavailable:
            # Never evaluated. Assume the device is fine rather than dropping it
            # on the basis of a check that never ran.
            return False
        return self.dataavailable[key] is False

    def t_addDataWarnings(self, *args):
        """Add the graph generation summary row at the bottom of the dashboard."""
        if self.datawarnings:
            title = f"Graph Generation Warnings ({len(self.datawarnings)})"
            content = "".join(f"&#9888; {escapeHTML(warn)}<br/>" for warn in self.datawarnings)
            collapsed = False
        else:
            title = "Graph Generation Warnings (0)"
            content = "No issues identified while generating this dashboard."
            collapsed = True
        row = self.t_addRow(*args, title=title, collapsed=collapsed)
        return self.addRowPanel(row, [self.t_addText("", content)])
