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
