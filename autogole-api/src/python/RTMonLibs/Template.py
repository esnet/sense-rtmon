#!/usr/bin/env python3
# pylint: disable=E1101
"""Grafana Template Generation"""
import copy
import os.path
from RTMonLibs.GeneralLibs import loadJson, dumpJson, dumpYaml, escape, _processName
from RTMonLibs.DiagramWorker import DiagramWorker

def clamp(n, minn, maxn):
    """Clamp the value between min and max"""
    return max(min(maxn, n), minn)

class Mermaid():
    """Mermaid Template Class"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        self.mermaid = ["graph LR"]
        self.links = []
        self.portnames = {}
        self.vlans = {}
        self.m_groups = {'Hosts': {}, 'Switches': {}}  # Group Hosts and Switches
        self.mac_addresses = {}
        self.orderlist = []
        self.orderlistports = []
        self.instance = None

    def _m_cleanCache(self):
        """Clean Cache"""
        self.links = []
        self.portnames = {}
        self.mermaid = ["graph LR"]
        self.m_groups = {'Hosts': {}, 'Switches': {}}
        self.mac_addresses = {}
        self.vlans = {}
        self.orderlist = []
        self.orderlistports = []
        self.instance = None

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
        if 'Mac' in hostdict and hostdict['Mac'] not in self.mac_addresses \
                and hostdict['Mac'] != "?mac?" \
                and hostdict['Mac'] != "?port_mac?":
            self.mac_addresses.setdefault(hostname, hostdict['Mac'])

    def _m_addBGP(self, item, ipkey, bgppeer):
        """Add BGP into Mermaid graph"""
        if not item.get('Site', None):
            return
        for intitem in self.instance.get('intents', []):
            for connections in intitem.get('json', {}).get('data', {}).get('connections', []):
                for terminal in connections.get('terminals', []):
                    if 'uri' not in terminal:
                        continue
                    if item['Site'] == terminal['uri'] and terminal.get(f'{ipkey.lower()}_prefix_list', None):
                        val = terminal[f'{ipkey.lower()}_prefix_list']
                        self.mermaid.append(f'        {bgppeer}_bgp{ipkey}(BGP_{ipkey})')
                        self._m_addLink(bgppeer, f'{bgppeer}_bgp{ipkey}')
                        self.mermaid.append(f'        {bgppeer}_bgp{ipkey}_peer({val})')
                        self._m_addLink(f'{bgppeer}_bgp{ipkey}', f'{bgppeer}_bgp{ipkey}_peer')

    def _m_addSwitch(self, item):
        uniqname = _processName(f'{item["Node"]}_{item["Name"]}')
        self.m_groups['Switches'].setdefault(item["Node"], {}).setdefault(item["Name"], {})
        self.m_groups['Switches'][item["Node"]][item["Name"]] = item
        self._m_recordMac(item)  # Record mac of switch interfaces
        if item.get('JointSite', False):
            self.mermaid.append(f'    subgraph "{item["JointSite"]}"')
            self.mermaid.append(f'        {uniqname}("{item["JointNetwork"]}")')
        else:
            self.mermaid.append(f'    subgraph "{item["Node"]}"')
            self.mermaid.append(f'        {uniqname}("{item["Name"]}")')
        if 'Peer' in item and item['Peer'] != "?peer?":
            self._m_addLink(uniqname, _processName(item['Peer']))
            if 'Vlan' in item and item['Vlan']:
                self._m_addVlan(f'{uniqname}_{item["Peer"]}', item['Vlan'])
        self._m_addPorts(_processName(item['Port']), uniqname)
        # Add IPv4/IPv6 on the switch
        for ipkey, ipdef in {'IPv4': '?port_ipv4?', 'IPv6': '?port_ipv6?'}.items():
            if ipkey in item and item[ipkey] != ipdef:
                uniqname = _processName(f'{item["Node"]}')
                self.mermaid.append(f'        {uniqname}_{ipkey}({item[ipkey]})')
                if item.get('Vlan'):
                    self.mermaid.append(f'        {uniqname}_vlan{item["Vlan"]}(vlan.{item["Vlan"]})')
                    self._m_addLink(_processName(item['Port']), f'{uniqname}_vlan{item["Vlan"]}')
                    self._m_addLink(f'{uniqname}_vlan{item["Vlan"]}', f'{uniqname}_{ipkey}')
                    # Add BGP Peering information
                    self._m_addBGP(item, ipkey, f'{uniqname}_{ipkey}')
        self.mermaid.append('    end')
        return uniqname

    def _m_addHost(self, host):
        uniqname = _processName(f'{host["Name"]}_{host["Interface"]}')
        self.m_groups['Hosts'].setdefault(host["Name"], {}).setdefault(host["Interface"], {})
        self.m_groups['Hosts'][host["Name"]][host["Interface"]] = host
        self.mermaid.append(f'    subgraph "{host["Name"]}"')
        self._m_recordMac(host)  # Record mac of host interface
        if 'Interface' in host:
            self.mermaid.append(f'        {uniqname}("{host["Interface"]}")')
            for ipkey, ipdef in {'IPv4': '?ipv4?', 'IPv6': '?ipv6?'}.items():
                if ipkey in host and host[ipkey] != ipdef:
                    self.mermaid.append(f'        {uniqname}_{ipkey}({host[ipkey]})')
                    if host.get('Vlan'):
                        self.mermaid.append(f'        {uniqname}_vlan{host["Vlan"]}(vlan.{host["Vlan"]})')
                        self._m_addLink(uniqname, f'{uniqname}_vlan{host["Vlan"]}')
                        self._m_addLink(f'{uniqname}_vlan{host["Vlan"]}', f'{uniqname}_{ipkey}')
                        self.m_groups['Hosts'].setdefault(host["Name"], {}).setdefault(f'vlan.{host["Vlan"]}', {})
        self.mermaid.append('    end\n')
        if 'Link' in host:
            self._m_addLink(uniqname, host['Link'])
            if 'Vlan' in host and host['Vlan']:
                self._m_addVlan(f'{uniqname}_{host["Link"]}', host['Vlan'])
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

    def _m_addItem(self, item):
        """Add Item to the list"""
        if item['Type'] == 'Host':
            self._m_addHost(item)
        elif item['Type'] == 'Switch':
            self._m_addSwitch(item)

    def _findHost(self, manifest, _nexthop, lastitem):
        for idx, item in enumerate(manifest["Ports"]):
            for hostdata in item.get('Host', []):
                tmphost = self.so_override(hostdata)
                tmpitem = self.so_override(item)
                tmphost['Type'] = 'Host'
                tmphost['Vlan'] = None if not tmpitem.get('Vlan') else tmpitem['Vlan']
                tmphost['Link'] = _processName(f'{tmpitem["Node"]}_{tmpitem["Name"]}')
                if item.get('Peer', '?peer?') == "?peer?":
                    item['PeerHost'] = tmphost['Name']
                self.orderlist.append(tmphost)
                del tmpitem['Host']
                tmpitem['Type'] = 'Switch'
                self.orderlist.append(tmpitem)
                return idx, tmpitem['Node'], tmpitem
        return None, None, lastitem

    def _findNode(self, manifest, node, lastitem):
        nextHop = ""
        delitems = []
        tmpitem = None
        for idx, item in enumerate(manifest["Ports"]):
            tmpitem = self.so_override(item)
            if tmpitem["Node"] == node:
                if 'Host' in tmpitem and tmpitem['Host']:
                    hostid, _, _ = self._findHost(manifest, None, tmpitem)
                    delitems.append(hostid)
                    continue
                tmpitem['Type'] = 'Switch'
                self.orderlist.append(tmpitem)
                if tmpitem['Peer'] != "?peer?" and item['Peer'] not in self.orderlistports:
                    tmpitem['Type'] = 'Switch'
                    self.orderlistports.append(tmpitem['Peer'])
                    nextHop = tmpitem['Peer']
                delitems.append(idx)
        return delitems, nextHop, tmpitem if tmpitem else lastitem

    def _findPeer(self, manifest, peer, lastitem):
        for idx, item in enumerate(manifest["Ports"]):
            tmpitem = self.so_override(item)
            if tmpitem["Port"] == peer:
                tmpitem['Type'] = 'Switch'
                self.orderlist.append(tmpitem)
                return idx, tmpitem['Node'], tmpitem
        return None, None, lastitem

    def findorder(self, manifest):
        """Find all orders of the manifest"""
        nexthop = None
        nexthoptype = 'Host'
        counter = 50
        lastitem = None
        loopcount = 5
        while len(manifest["Ports"]) > 0:
            if nexthoptype == 'Host':
                hostid, nexthop, lastitem = self._findHost(manifest, nexthop, lastitem)
                if hostid is not None:
                    del manifest["Ports"][hostid]
                    nexthoptype = 'Node'
                    continue
            if nexthoptype == 'Node':
                hostid, nexthop, lastitem = self._findNode(manifest, nexthop, lastitem)
                if hostid:
                    hostid.sort(reverse=True) # Deletion should happen from the last item
                    for idx in hostid:
                        del manifest["Ports"][idx]
                    nexthoptype = 'Peer'
                else:
                    nexthoptype = 'Host'
                continue
            if nexthoptype == 'Peer':
                hostid, nexthop, lastitem = self._findPeer(manifest, nexthop, lastitem)
                nexthoptype = 'Node'
                if hostid is not None:
                    del manifest["Ports"][hostid]
                    nexthoptype = 'Node'
                continue
            if not nexthop and nexthoptype == 'Host' and lastitem:
                nexthop = lastitem['Node']
                nexthoptype = 'Node'
            counter -= 1
            if counter < 0:
                self.logger.warning("Counter reached 0, restarting loop with findNode")
                self.logger.warning(f"Remaining items: {manifest['Ports']}")
                # Use findNode and take the first item from the list
                loopcount -= 1
                if loopcount < 0:
                    self.logger.error("Loopcount reached 0, breaking")
                    break
                nexthoptype = 'Node'
                nexthop = manifest["Ports"][0]["Node"]
                counter = 50

    def m_getMermaidContent(self, instance, manifest):
        """Create Mermaid Template"""
        self._m_cleanCache()
        self.instance = instance
        self.findorder(manifest)
        for item in self.orderlist:
            self._m_addItem(item)
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
        self.annotationids = []

    def _clean(self):
        """Clean previous generated data"""
        self.generated = {}
        self.annotationids = []
        self.nextid = 0

    def __getTitlesUrls(self, site, link):
        """Get Titles and URLs"""
        title = link.get('title', "Link-Title-Not-Present-in-Config")
        url = link.get('url', "https://link-not-present-in-config")
        title = title.replace("$$REPLACEMESITENAME$$", site)
        url = url.replace("$$REPLACEMESITENAME$$", site)
        return title, url

    def _getNextID(self, recordAnnotations=False):
        """Get Next ID"""
        self.nextid += 1
        if recordAnnotations:
            self.annotationids.append(self.nextid)
        return self.nextid

    def _getNextRowID(self):
        """Increase Row ID"""
        self.nextid += 100
        return self.nextid

    def addRowPanel(self, row, panels, recordAnnotations=False):
        """Add Panel to the Row (Depending on collapsed or not)"""
        # https://github.com/grafana/grafana/issues/50855
        out = []
        if not row['collapsed']:
            out.append(row)
        for pan in panels:
            pan["id"] = self._getNextID(recordAnnotations)
            if 'gridPos' not in pan:
                pan["gridPos"] = self.gridPos
            if row['collapsed']:
                row["panels"].append(pan)
            else:
                out.append(pan)
        if row['collapsed']:
            out.append(row)
        return out

    def _t_getDataSourceUid(self, *_args):
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

    def t_addImageCollapsibleRow(self, image_url, title="Network Topology Image"):
        """Add an Image Panel to a Collapsible Row"""
        row = self.t_addRow(title=f"{title} Row", collapsed=True)
        panel = self.t_addImagePanel(image_url, title=title)
        return self.addRowPanel(row, [panel], recordAnnotations=False)


    def t_addImagePanel(self, image_url, title="Image Panel"):
        """Add an Image Panel to the Dashboard"""
        panel = {
            "type": "text",
            "title": title,
            "options": {
                "content": f"<div style='text-align:center;'><img src='{image_url}' style='max-width:100%; height:auto;'></div>",
            },
            "gridPos": {"x": 0, "y": 0, "w": 24, "h": 30},
            "id": self._getNextID()
        }
        return panel

    def t_addRow(self, *_args, **kwargs):
        """Add Row to the Dashboard"""
        out = self._t_loadTemplate("row.json")
        out["title"] = kwargs.get('title', "Row Title Not Present")
        out["id"] = self._getNextRowID()
        return out

    def t_addLinks(self, *_args, **kwargs):
        """Add Links to the Dashboard"""
        def _getSiteDashbUID(site):
            for key in ['NSI', 'SiteRM']:
                uid = self.dashboards.get(key, {}).get(site, {}).get('uid', None)
                if uid:
                    return uid
            return None

        ret = []
        out = self._t_loadTemplate("links.json")
        sites = []
        # First need to identify all sites (only uniques, as it can repeat)
        for sitehost, _interfaces in self.m_groups['Hosts'].items():
            sitename = sitehost.split(":")[0]
            if sitename in self.dashboards and sitename not in sites:
                sites.append(sitename)
        for sitehost, _interfaces in self.m_groups['Switches'].items():
            sitename = sitehost.split(":")[0]
            if (sitename in self.dashboards.get('SiteRM', {}) or sitename in self.dashboards.get('NSI', {})) \
                    and sitename not in sites:
                sites.append(sitename)

        # Add dynamic urls from configuration and replace sitename with site
        addedUrls = []
        for site in sites:
            tmpcopy = copy.deepcopy(out)
            tmpcopy["title"] = f"Site Monitoring: {site}"
            uid = _getSiteDashbUID(site)
            if not uid:
                self.logger.debug(f'Site {site} dashboard does not exist in Grafana. Will not add link back.')
                continue
            tmpcopy["url"] = f"{self.config['grafana_host']}/d/{uid}"
            ret.append(tmpcopy)
            for link in self.config['template_links']:
                title, url = self.__getTitlesUrls(site, link)
                if url not in addedUrls:
                    tmpcopy = copy.deepcopy(out)
                    tmpcopy["title"] = title
                    tmpcopy["url"] = url
                    print(tmpcopy)
                    ret.append(tmpcopy)
                addedUrls.append(url)
        if kwargs.get('oscarsid', '') and self.config.get('oscars_base_url', ''):
            oscarsid = kwargs['oscarsid']
            tmpcopy = copy.deepcopy(out)
            tmpcopy["title"] = f"Oscars monitoring: {oscarsid}"
            tmpcopy["url"] = f"{self.config['oscars_base_url']}{oscarsid}"
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
            out += self.addRowPanel(row, panels, True)
        return out

    def t_createSwitchFlow(self, *args):
        """Create Switch Flow Template"""
        def findIntf(interfaces):
            """Find Interface"""
            intfs = []
            for intfname, intfdata in interfaces.items():

                if "?port_name?" == intfname:
                    continue
                if "JointNetwork" in intfdata:
                    print(f"JointNetwork: {intfdata['JointNetwork']}")
                    # ifDescr=~"newy32aoa-cr6::1/1/c13/1|newy32aoa-cr6::.*1/1/c13/1-2015"
                    # 'JointNetwork': 'newy32aoa-cr6|1_1_c13_1|fabric'
                    splitdata = intfdata['JointNetwork'].split("|")
                    if len(splitdata) >= 2:
                        intfs.append(f"{splitdata[0]}.*{splitdata[1].replace('_', '/')}")
                        intfs.append(f"{splitdata[0]}.*{splitdata[1].replace('_', '/')}-{intfdata['Vlan']}")
                    if len(splitdata) == 3:
                        intfs.append(splitdata[2])
                else:
                    intfs.append(intfname)
                    # Add also lowercase and space removed intf names
                    # https://github.com/esnet/sense-rtmon/issues/128
                    intfs.append(intfname.lower())
                    intfs.append(intfname.replace(" ", ""))
                    intfs.append(intfname.lower().replace(" ", ""))
            intfline = "|".join(intfs)
            return intfline
        out = []
        for sitehost, interfaces in self.m_groups['Switches'].items():
            try:
                sitename = sitehost.split(":")[0]
                hostname = sitehost.split(":")[1]
            except IndexError as ex:
                self.logger.error(f"Got Exception: {ex}")
                self.logger.error(f"Sitehost: {sitehost}")
                self.logger.error(f"Interfaces: {interfaces}")
                self.logger.error("This happens for Sites/Switches not exposing correct Sitename/Port. Are you missing an override?")
                raise Exception("Sitehost not in correct format") from ex
            sitename = sitehost.split(":")[0]
            hostname = sitehost.split(":")[1]
            intfline = findIntf(interfaces)
            row = self.t_addRow(*args, title=f"Switch Flow Summary: {sitehost}")
            panels = dumpJson(self._t_loadTemplate("switchflow.json"), self.logger)
            panels = panels.replace("REPLACEME_DATASOURCE", str(self.t_dsourceuid))
            panels = panels.replace("REPLACEME_SITENAME", sitename)
            panels = panels.replace("REPLACEME_HOSTNAME", hostname)
            panels = panels.replace("REPLACEME_INTERFACE", escape(intfline))
            panels = loadJson(panels, self.logger)
            out += self.addRowPanel(row, panels, True)
        return out

    def t_createMermaid(self, *args):
        """Create Mermaid Template"""
        # Identify all peers
        self.so_mappeers(args[1])
        row = self.t_addRow(*args, title="End-to-End Flow Monitoring")
        panel = self._t_loadTemplate("mermaid.json")
        mermaid = self.m_getMermaidContent(*args)
        panel["options"]["content"] = "\n".join(mermaid)
        # Need to add correct size for the panel
        totalHeight = 12 + len(self.m_groups['Hosts']) + len(self.m_groups['Switches'])
        panel["gridPos"]["h"] = clamp(totalHeight, 14, 24)
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
            if 'Vlan' in intfdata and intfdata['Vlan']:
                vlan = intfdata['Vlan']
                for mhost, macaddr in self.mac_addresses.items():
                    if mhost != hostname:
                        query = copy.deepcopy(origin_query)
                        query['datasource']['uid'] = str(self.t_dsourceuid)
                        query['expr'] = f'sum(arp_state{{HWaddress=~"{macaddr}.*",Hostname="{hostname}",sitename="{sitename}",Device="vlan.{vlan}"}}) OR on() vector(0)'
                        query['legendFormat'] = f'MAC address of {mhost} end visible in arptable under vlan.{vlan}'
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
                query['expr'] = f'sum(mac_table_info{{sitename="{sitename}",hostname="{hostname}", macaddress="{macaddr}", vlan="{vlan}"}}) OR on() vector(0)'
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
        return self.addRowPanel(row, out, True)

    def t_createTemplate(self, *args, **kwargs):
        """Create Grafana Template"""
        self._clean()
        self._t_getDataSourceUid(*args)
        self.generated = self.t_createDashboard(*args, **kwargs)
        # Add Mermaid (Send copy of args, as t_createMermaid will modify it by del items)
        orig_args = copy.deepcopy(args)
        self.generated['panels'] += self.t_createMermaid(*orig_args)
        ##GENERATE DIAGRAMS

        try: 
            diagram_filename = f"{self.config.get('image_dir', '/srv/images')}/diagram_{kwargs['referenceUUID']}"
            self.d_createGraph(diagram_filename, self.orderlist)
            self.logger.info(f"Diagram saved at {diagram_filename}.png")
        except IOError as ex:
            self.logger.error('Failed to create diagram: %s', ex)

        # Add Links on top of the page
        self.generated['links'] = self.t_addLinks(*args, **kwargs)
        # Add Debug Info (manifest, instance)
        self.generated['panels'] += self.t_addDebug(*args)
        # Add Host Flow
        self.generated['panels'] += self.t_createHostFlow(*args)
        # Add Switch Flow
        self.generated['panels'] += self.t_createSwitchFlow(*args)
        # Add L2 Debugging
        self.generated['panels'] += self.t_addL2Debugging(*args)
        #Image Panel
        base_image_url = self.config.get('baseImageURL', 'http://localhost:8000/images')
        image_url = f"{base_image_url}/diagram_{kwargs['referenceUUID']}.png"
        self.generated['panels'] += self.t_addImageCollapsibleRow(image_url, title="Network Topology Image")

        return {"dashboard": self.generated}, {"uid": self.generated['uid'], "annotation_panels": self.annotationids}
