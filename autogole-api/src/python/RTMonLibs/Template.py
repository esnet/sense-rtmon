#!/usr/bin/env python3
"""Grafana Template Generation"""
import copy
import os.path
from RTMonLibs.GeneralLibs import loadJson, dumpJson, dumpYaml

def _processName(name):
    """Process Name for Mermaid and replace all special chars with _"""
    for repl in [[" ", "_"], [":", "_"], ["/", "_"], ["-", "_"], [".", "_"], ["?", "_"]]:
        name = name.replace(repl[0], repl[1])
    return name

def clamp(n, minn, maxn):
    """Clamp the value between min and max"""
    return max(min(maxn, n), minn)

class Mermaid():
    """Mermaid Template Class"""
    def __init__(self, **kwargs):
        super().__init__()
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        self.mermaid = []
        self.links = []
        self.portnames = {}
        self.vlans = {}
        self.m_groups = {'Hosts': {}, 'Switches': {}}  # Group Hosts and Switches
        self.mac_addresses = {}
        self.totalpoints = 0

    def _m_cleanCache(self):
        """Clean Cache"""
        self.links = []
        self.portnames = {}
        self.mermaid = ["graph TB"]
        self.m_groups = {'Hosts': {}, 'Switches': {}}
        self.mac_addresses = {}

    def _m_addLink(self, val1, val2):
        if [val1, val2] not in self.links and [val2, val1] not in self.links:
            self.links.append([val1, val2])

    def _m_addPorts(self, port, portname):
        self.portnames[port] = portname

    def _m_addVlan(self, link, vlan):
        self.vlans[_processName(link)] = vlan

    def _m_recordMac(self, hostdict):
        """Record mac into var"""
        try:
            hostname = hostdict['Name'].split(':')[1]
        except IndexError as ex:
            hostname = hostdict['Name']
            self.logger.debug(f"Got Exception: {ex}")

        if 'MAC' in hostdict and hostdict['MAC'] not in self.mac_addresses and hostdict['MAC'] != "?mac?":
            self.mac_addresses.setdefault(hostname, hostdict['MAC'])

    def _m_addSwitch(self, item):
        uniqname = _processName(f'{item["Node"]}_{item["Name"]}')
        self.m_groups['Switches'].setdefault(item["Node"], {}).setdefault(item["Name"], {})
        self.m_groups['Switches'][item["Node"]][item["Name"]] = item
        self.mermaid.append(f'    subgraph "{item["Node"]}"')
        self.mermaid.append(f'        {uniqname}("{item["Name"]}")')
        self.mermaid.append('    end')
        if 'Peer' in item and item['Peer'] != "?peer?":
            self._m_addLink(uniqname, _processName(item['Peer']))
            if 'Vlan' in item and item['Vlan']:
                self._m_addVlan(f'{uniqname}_{item["Peer"]}', item['Vlan'])
        self._m_addPorts(_processName(item['Port']), uniqname)
        return uniqname

    def _m_addHost(self, host, vlan):
        uniqname = _processName(f'{host["Name"]}_{host["Interface"]}')
        self.m_groups['Hosts'].setdefault(host["Name"], {}).setdefault(host["Interface"], {})
        self.m_groups['Hosts'][host["Name"]][host["Interface"]] = host
        self.mermaid.append(f'    subgraph "{host["Name"]}"')
        self._m_recordMac(host)  # Record mac of host interface
        if 'Interface' in host:
            self.mermaid.append(f'        {uniqname}("{host["Interface"]}")')
            if 'IPv4' in host:
                self.mermaid.append(f'        {uniqname}_IPv4({host["IPv4"]})')
                if vlan:
                    self.mermaid.append(f'        {uniqname}_vlan{vlan}(vlan.{vlan})')
                    self._m_addLink(uniqname, f'{uniqname}_vlan{vlan}')
                    self._m_addLink(f'{uniqname}_vlan{vlan}', f'{uniqname}_IPv4')
                    self.m_groups['Hosts'].setdefault(host["Name"], {}).setdefault(f'vlan.{vlan}', {})
        self.mermaid.append('    end\n')
        return uniqname

    def _m_getVlan(self, link):
        """Get Vlan for link pair"""
        for tmp in [f"{link[0]}_{link[1]}", f"{link[1]}_{link[0]}"]:
            if tmp in self.vlans:
                return self.vlans[tmp]
        return None

    def _m_createMermaidLinks(self):
        """Create Mermaid Links"""
        added = []
        for link in self.links:
            end1 = link[0] if link[0] not in self.portnames else self.portnames[link[0]]
            end2 = link[1] if link[1] not in self.portnames else self.portnames[link[1]]
            vlan = self._m_getVlan(link)
            if [end1, end2, vlan] in added:
                continue
            if vlan:
                line = f'    {end1}<--{vlan}-->{end2}'
            else:
                line = f'    {end1}<-->{end2}'
            if line not in self.mermaid:
                self.mermaid.append(line)
            added.append([end1, end2, vlan])
            added.append([end2, end1, vlan])

    def m_getMermaidContent(self, manifest):
        """Create Mermaid Template"""
        self._m_cleanCache()
        for item in manifest["Ports"]:
            if 'Host' in item:
                uniqname = ""
                for hostdata in item['Host']:
                    vlan = None if not item.get('Vlan') else item['Vlan']
                    uniqname = self._m_addHost(hostdata, vlan)
                    if uniqname:
                        self._m_addLink(uniqname, _processName(f'{item["Node"]}_{item["Name"]}'))
                    if vlan:
                        self._m_addVlan(f'{uniqname}_{item["Node"]}_{item["Name"]}', item['Vlan'])
                        self._m_addVlan(f'{uniqname}_IPv4_{item["Node"]}_{item["Name"]}', item['Vlan'])
            self._m_addSwitch(item)
        # Now we can create all links
        self._m_createMermaidLinks()
        for line in self.mermaid:
            self.logger.debug(line)
        return self.mermaid

class Template():
    """Autogole SENSE Grafana RTMon API"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        self.templatePath = self.config['template_path']
        self.generated = {}
        self.t_dsourceuid = 0
        self.nextid = 0
        self.gridPos = {"x": 0, "y": 0, "w": 24, "h": 8}

    def _getNextID(self):
        """Get Next ID"""
        self.nextid += 1
        return self.nextid

    def _getNextRowID(self):
        """Increase Row ID"""
        self.nextid += 100
        return self.nextid

    def addRowPanel(self, row, panels):
        """Add Panel to the Row (Depending on collapsed or not)"""
        # https://github.com/grafana/grafana/issues/50855
        out = []
        if not row['collapsed']:
            out.append(row)
        for pan in panels:
            pan["id"] = self._getNextID()
            if 'gridPos' not in pan:
                pan["gridPos"] = self.gridPos
            if row['collapsed']:
                row["panels"].append(pan)
            else:
                out.append(pan)
        if row['collapsed']:
            out.append(row)
        return out

    def _t_getDataSourceUid(self, *args):
        """Get Data Source UID"""
        # TODO: We need a way for Orchestrator to tell us if this is real time (5sec resolution)
        # or historical (1min resolution)
        # For now return the historical one
        name = self.config.get('data_sources', {}).get('general', 'Prometheus')
        self.t_dsourceuid = self.datasources.get(name, {}).get('uid', 1)

    def _t_loadTemplate(self, templateName):
        """Load Template"""
        template = None
        with open(os.path.join(self.templatePath, templateName), 'r', encoding="utf-8") as fd:
            template = loadJson(fd.read(), self.logger)
        return template

    def t_addRow(self, *args, **kwargs):
        """Add Row to the Dashboard"""
        out = self._t_loadTemplate("row.json")
        out["title"] = kwargs.get('title', "Row Title Not Present")
        out["id"] = self._getNextRowID()
        return out

    def t_addLinks(self, *_args):
        """Add Links to the Dashboard"""
        if not self.config.get('template_links', []):
            return []
        ret = []
        out = self._t_loadTemplate("links.json")
        for link in self.config['template_links']:
            tmpcopy = copy.deepcopy(out)
            tmpcopy["title"] = link.get('title', "Link-Title-Not-Present-in-Config")
            tmpcopy["url"] = link.get('url', "https://link-not-present-in-config")
            ret.append(tmpcopy)
        # Add all Monitoring links to SiteRM/NetworkRM
        sites = []
        # First need to identify all sites (only uniques, as it can repeat)
        for sitehost, _interfaces in self.m_groups['Hosts'].items():
            sitename = sitehost.split(":")[0]
            if sitename in self.dashboards and sitename not in sites:
                sites.append(sitename)
        for sitehost, _interfaces in self.m_groups['Switches'].items():
            sitename = sitehost.split(":")[0]
            if sitename in self.dashboards and sitename not in sites:
                sites.append(sitename)
        # For all sites - add the monitoring link
        for site in sites:
            tmpcopy = copy.deepcopy(out)
            tmpcopy["title"] = f"Site Monitoring: {site}"
            tmpcopy["url"] = f"{self.config['grafana_host']}/d/{self.dashboards[site]['uid']}"
            ret.append(tmpcopy)
        return ret


    def t_addText(self, *args):
        """Add Text Panel to the Dashboard"""
        out = self._t_loadTemplate("text.json")
        out["id"] = self._getNextID()
        out["title"] = args[0]
        out["options"]["content"] = args[1]
        return out

    def t_createDashboard(self, *args, **kwargs):
        """Load Dashboard Template and add all args as needed"""
        out = self._t_loadTemplate("dashboard.json")
        # Update title;
        title = f'{args[0]["alias"]}|Flow: {args[0]["intents"][0]["id"]}|{args[0]["timestamp"]}'
        out["title"] = title
        for key in ['referenceUUID', 'orchestrator', 'submission']:
            if key in kwargs:
                out['tags'].append(kwargs[key])
        out['tags'].append(self.config['template_tag'])
        out["uid"] = args[0]["intents"][0]["id"]
        return out

    def t_createHostFlow(self, *args):
        """Create Host Flow Template"""
        out = []
        for sitehost, interfaces in self.m_groups['Hosts'].items():
            sitename = sitehost.split(":")[0]
            hostname = sitehost.split(":")[1]
            intfline = "|".join(interfaces.keys())
            row = self.t_addRow(*args, title=f"Host Flow Summary: {sitehost}")
            panels = dumpJson(self._t_loadTemplate("hostflow.json"), self.logger)
            panels = panels.replace("REPLACEME_DATASOURCE", str(self.t_dsourceuid))
            panels = panels.replace("REPLACEME_SITENAME", sitename)
            panels = panels.replace("REPLACEME_HOSTNAME", hostname)
            panels = panels.replace("REPLACEME_INTERFACE", intfline)
            panels = loadJson(panels, self.logger)
            out += self.addRowPanel(row, panels)
        return out

    def t_createSwitchFlow(self, *args):
        """Create Switch Flow Template"""
        out = []
        for sitehost, interfaces in self.m_groups['Switches'].items():
            sitename = sitehost.split(":")[0]
            hostname = sitehost.split(":")[1]
            intfline = "|".join(interfaces.keys())
            row = self.t_addRow(*args, title=f"Switch Flow Summary: {sitehost}")
            panels = dumpJson(self._t_loadTemplate("switchflow.json"), self.logger)
            panels = panels.replace("REPLACEME_DATASOURCE", str(self.t_dsourceuid))
            panels = panels.replace("REPLACEME_SITENAME", sitename)
            panels = panels.replace("REPLACEME_HOSTNAME", hostname)
            panels = panels.replace("REPLACEME_INTERFACE", intfline)
            panels = loadJson(panels, self.logger)
            out += self.addRowPanel(row, panels)
        return out

    def t_createMermaid(self, *args):
        """Create Mermaid Template"""
        row = self.t_addRow(*args, title="End-to-End Flow Monitoring")
        panel = self._t_loadTemplate("mermaid.json")
        mermaid = self.m_getMermaidContent(args[1])
        panel["options"]["content"] = "\n".join(mermaid)
        # Need to add correct size for the panel
        totalHeight = 18 + (len(self.m_groups['Hosts'])*2) + (len(self.m_groups['Switches'])*2)
        panel["gridPos"]["h"] = clamp(totalHeight, 18, 48)
        return self.addRowPanel(row, [panel])

    def t_addDebug(self, *args):
        """Add Debug Info to the Dashboard"""
        out = []
        row = self.t_addRow(*args, title="Debug Info (SENSE-O Output)")
        # Force row to be collapsed
        row["collapsed"] = True
        # Add Instance information
        textout = ""
        for line in dumpYaml(args[0], self.logger).split("\n"):
            # Identify key, val
            tmpval = line.split(":", 1)
            key = tmpval[0]
            val = tmpval[1] if len(tmpval) > 1 else ""
            key = key.replace(" ", "&nbsp;")
            val = val.replace(" ", "&nbsp;")
            textout += f"<b>{key}:</b>  {val}<br/>"
        textGraph = self.t_addText("Instance from SENSE-O", textout)
        # Add Manifest information
        textout = ""
        for line in dumpYaml(args[1], self.logger).split("\n"):
            tmpval = line.split(":", 1)
            key = tmpval[0]
            val = tmpval[1] if len(tmpval) > 1 else ""
            key = key.replace(" ", "&nbsp;")
            val = val.replace(" ", "&nbsp;")
            textout += f"<b>{key}:</b>  {val}<br/>"
        textGraph1 = self.t_addText("Manifest from SENSE-O", textout)
        out += self.addRowPanel(row, [textGraph, textGraph1])
        return out

    def _t_addHostL2Debugging(self, sitehost, interfaces, refid):
        """Add L2 Debugging for Host"""
        queries = []
        sitename = sitehost.split(":")[0]
        hostname = sitehost.split(":")[1]
        origin_query = self._t_loadTemplate("l2state-query.json")
        query = copy.deepcopy(origin_query)
        # Add state and check if it receives information from snmp monitoring
        #    count(arp_state{sitename = "NRM_CENIC"}) OR on() vector(0)
        query['datasource']['uid'] = str(self.t_dsourceuid)
        query['expr'] = f'count(arp_state{{sitename = "{sitename}"}}) OR on() vector(0)'
        query['legendFormat'] = f'SNMP Data available for {sitename} {hostname}'
        query['refId'] = f'A{refid}'
        refid += 1
        queries.append(query)
        # If IPv6 - do node_network_address_info and check if IP is set
        for _intf, intfdata in interfaces.items():
            for items in [['IPv6', '?ipv6?'], ['IPv4', '?ipv4?']]:
                if items[0] in intfdata and intfdata[items[0]] != items[1]:
                    query = copy.deepcopy(origin_query)
                    query['datasource']['uid'] = str(self.t_dsourceuid)
                    query['expr'] = f'node_network_address_info{{instance=~"{hostname}.*",sitename="{sitename}", address=~"{intfdata[items[0]].split("/")[0]}"}}'
                    query['legendFormat'] = f'{items[0]} Address present on {sitename} {hostname}'
                    query['refId'] = f'A{refid}'
                    refid += 1
                    queries.append(query)
        for mhost, macaddr in self.mac_addresses.items():
            if mhost != hostname:
                query = copy.deepcopy(origin_query)
                query['datasource']['uid'] = str(self.t_dsourceuid)
                query['expr'] = f'sum(arp_state{{HWaddress=~"{macaddr}.*"}}) OR on() vector(0)'
                query['legendFormat'] = f'MAC address of {mhost} end visible in arptable'
                query['refId'] = f'A{refid}'
                refid += 1
                queries.append(query)
        panel = self._t_loadTemplate("l2state.json")
        panel['id'] = self._getNextID()
        panel['title'] = f"L2 Debugging for Host: {sitehost}"
        panel['targets'] = queries
        panel['datasource']['uid'] = str(self.t_dsourceuid)
        panel['gridPos']['h'] = 4 + len(queries)
        return [panel]

    def _t_addSwitchL2Debugging(self, sitehost, interfaces, refid):
        """Add L2 Debugging for Switch"""
        queries = []
        sitename = sitehost.split(":")[0]
        hostname = sitehost.split(":")[1]
        origin_query = self._t_loadTemplate("l2state-query.json")
        query = copy.deepcopy(origin_query)
        # Add state and check if it receives information from snmp monitoring
        #    count(interface_statistics{sitename = "NRM_CENIC", hostname = "$switch"})
        query['datasource']['uid'] = str(self.t_dsourceuid)
        query['expr'] = f'count(interface_statistics{{sitename="{sitename}", hostname="{hostname}"}}) OR on() vector(0)'
        query['legendFormat'] = f'SNMP Data available for {sitename} {hostname}'
        query['refId'] = f'A{refid}'
        refid += 1
        queries.append(query)
        # For each host mac address - do mac_table_info
        vlans = []
        for _intf, intfdata in interfaces.items():
            if 'Vlan' in intfdata and intfdata['Vlan'] not in vlans:
                vlans.append(intfdata['Vlan'])
        for vlan in vlans:
            for mhost, macaddr in self.mac_addresses.items():
                query = copy.deepcopy(origin_query)
                query['datasource']['uid'] = str(self.t_dsourceuid)
                query['expr'] = f'sum(mac_table_info{{hostname="{hostname}", macaddress="{macaddr}", vlan="{vlan}"}}) OR on() vector(0)'
                query['legendFormat'] = f'MAC address of {mhost} visible in mac table ({vlan})'
                query['refId'] = f'A{refid}'
                refid += 1
                queries.append(query)
        panel = self._t_loadTemplate("l2state.json")
        panel['id'] = self._getNextID()
        panel['title'] = f"L2 Debugging for Switch: {sitehost}"
        panel['targets'] = queries
        panel['datasource']['uid'] = str(self.t_dsourceuid)
        panel['gridPos']['h'] = 4 + len(queries)
        return [panel]

    def t_addL2Debugging(self, *args):
        """Add L2 Debugging to the Dashboard"""
        out = []
        row = self.t_addRow(*args, title="L2 Debugging:")
        # For each host if available:
        refID = 0
        for sitehost, interfaces in self.m_groups['Hosts'].items():
            self.logger.debug(f"Adding L2 Debugging for Host: {sitehost}, {interfaces}")
            out += self._t_addHostL2Debugging(sitehost, interfaces, refID)
        # For each switch:
        for sitehost, interfaces in self.m_groups['Switches'].items():
            self.logger.debug(f"Adding L2 Debugging for Switch: {sitehost}, {interfaces}")
            out += self._t_addSwitchL2Debugging(sitehost, interfaces, refID)
        # Add state and check if it receives information from snmp monitoring
        #     count(interface_statistics{sitename = "NRM_CENIC", hostname = "$switch"})
        # For each host mac address - do mac_table_info
        #     sum(mac_table_info{hostname="aristaeos_s0", macaddress="ec:0d:9a:c1:ba:60", vlan="3608"}) OR on() vector(0)
        return self.addRowPanel(row, out)

    def t_createTemplate(self, *args, **kwargs):
        """Create Grafana Template"""
        self.generated = {}
        self.nextid = 0
        self._t_getDataSourceUid(*args)
        self.generated = self.t_createDashboard(*args, **kwargs)
        # Add Mermaid
        #self.t_createMermaid(*args)
        self.generated['panels'] += self.t_createMermaid(*args)
        # Add Links on top of the page
        self.generated['links'] = self.t_addLinks(*args)
        # Add Debug Info (manifest, instance)
        self.generated['panels'] += self.t_addDebug(*args)
        # Add Host Flow
        self.generated['panels'] += self.t_createHostFlow(*args)
        # Add Switch Flow
        self.generated['panels'] += self.t_createSwitchFlow(*args)
        # Add L2 Debugging
        self.generated['panels'] += self.t_addL2Debugging(*args)
        return {"dashboard": self.generated}
