"""
DiagramWorker Class for Network Topology Visualization

This module contains the DiagramWorker class, which generates network topology diagrams 
by processing input data that includes hosts and switches. It uses the 'diagrams' library 
to visualize network components and their interconnections.
"""
import os
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from RTMonLibs.GeneralLibs import _processName

class DiagramWorker:
    """
    DiagramWorker class is responsible for generating network topology diagrams
    using the input data that contains host and switch information. The class
    identifies and visualizes links between network components.
    """
    HOST_ICON_PATH = '/srv/icons/host.png'
    SWITCH_ICON_PATH = '/srv/icons/switch.png'

    def __init__(self, indata):
        """
        Initialize the DiagramWorker with input data.

        :param indata: List of dictionaries containing host and switch details.
        """
        self.indata = indata
        self.objects = {}
        self.added = {}
        self.linksadded = set()
        self.popreverse = None

    def d_find_item(self, fval, fkey):
        """Find Item where fkey == fval"""
        for key, vals in self.objects.items():
            if vals.get('data', {}).get(fkey, '') == fval:
                return key, vals
        return None, None

    @staticmethod
    def d_LinkLabel(vals1, vals2):
        """Get Link Label"""
        label = ""
        if vals1.get('data', {}).get('Type', '') == "Host":
            label = f"Port1: {vals1['data']['Interface']}"
        elif vals1.get('data', {}).get('Type', '') == "Switch":
            label = f"Port1: {vals1['data']['Name']}"
        # Get second side info:
        if vals2.get('data', {}).get('Type', '') == "Host":
            label += f"\nPort2: {vals2['data']['Interface']}"
        elif vals2.get('data', {}).get('Type', '') == "Switch":
            label += f"\nPort2: {vals2['data']['Name']}"
        if vals1.get('data', {}).get('Vlan', None):
            label += f"\nVlan: {vals1['data']['Vlan']}"
        elif vals2.get('data', {}).get('Vlan', None):
            label += f"\nVlan: {vals2['data']['Vlan']}"
        return label

    def d_addLink(self, val1, val2, key, fkey):
        """Add Link between 2 objects"""
        if val1 and val2 and key and fkey:
            if key == fkey:
                return

            link_keys = tuple(sorted([key, fkey]))
            if link_keys in self.linksadded:
                return
            self.linksadded.add(link_keys)

            val1["obj"] >> Edge(label=self.d_LinkLabel(val1, val2)) << val2["obj"]

    def d_addLinks(self):
        """Identify Links between items"""
        for key, vals in self.objects.items():
            data_type = vals.get('data', {}).get('Type', '')
            if data_type == "Host":
                fKey, fItem = self.d_find_item(key, 'PeerHost')
                if fKey and fItem:
                    self.d_addLink(vals, fItem, key, fKey)
            elif data_type == "Switch":
                if 'Peer' in vals.get('data', {}) and vals['data']['Peer'] != "?peer?":
                    fKey, fItem = self.d_find_item(vals['data']['Peer'], "Port")
                    if fKey and fItem:
                        self.d_addLink(vals, fItem, key, fKey)
                elif 'PeerHost' in vals.get('data', {}):
                    fKey = vals['data']['PeerHost']
                    fItem = self.objects.get(fKey)
                    if fItem:
                        self.d_addLink(vals, fItem, key, fKey)

    def d_addHost(self, item):
        """
        Add a host to the network diagram.

        :param item: Dictionary containing host details.
        :return: Diagram object representing the host.
        """
        name = f"Host: {item['Name'].split(':')[1]}"
        name += f"\nInterface: {item['Interface']}"
        name += f"\nVlan: {item['Vlan']}"
        if 'IPv4' in item and item['IPv4'] != "?ipv4?":
            name += f"\nIPv4: {item['IPv4']}"
        if 'IPv6' in item and item['IPv6'] != "?ipv6?":
            name += f"\nIPv6: {item['IPv6']}"

        worker = Custom(name, self.HOST_ICON_PATH)
        self.objects[item['Name']] = {"obj": worker, "data": item}
        return worker

    def d_addSwitch(self, item):
        """
        Add a switch to the network diagram.

        :param item: Dictionary containing switch details.
        :return: Diagram object representing the switch.
        """
        if item['Node'] in self.added:
            self.objects[item['Port']] = {
                                            "obj": self.objects[self.added[item['Node']]]["obj"],
                                            "data": item
                                         }
            return
        switch1 = Custom(item['Node'].split(":")[1], self.SWITCH_ICON_PATH)
        if 'Peer' in item and item['Peer'] != "?peer?":
            self.added[item['Node']] = item['Port']
            self.objects[item['Port']] = {"obj": switch1, "data": item}
        elif 'PeerHost' in item:
            uniqname = _processName(f'{item["Node"]}_{item["Name"]}')
            self.added[item['Node']] = uniqname
            self.objects[uniqname] = {"obj": switch1, "data": item}
         # Add IPv4/IPv6 on the switch
        for ipkey, ipdef in {'IPv4': '?port_ipv4?', 'IPv6': '?port_ipv6?'}.items():
            if ipkey in item and item[ipkey] != ipdef:
                ip_node_name = f"{item['Node']}_{ipkey}"
                ip_label = item[ipkey]
                ip_node = Custom(ip_label, self.HOST_ICON_PATH)
                self.objects[ip_node_name] = {"obj": ip_node, "data": {}}
                # Add edge between switch and IP node
                self.d_addLink(self.objects[item['Port']], self.objects[ip_node_name], item['Port'], ip_node_name)
                if item.get('Vlan'):
                    vlan_node_name = f"{item['Node']}_vlan{item['Vlan']}"
                    vlan_label = f"vlan.{item['Vlan']}"
                    vlan_node = Custom(vlan_label, self.SWITCH_ICON_PATH)
                    self.objects[vlan_node_name] = {"obj": vlan_node, "data": {}}
                    self.d_addLink(self.objects[item['Port']], self.objects[vlan_node_name], item['Port'], vlan_node_name)
                    self.d_addLink(self.objects[vlan_node_name], self.objects[ip_node_name], vlan_node_name, ip_node_name)
                    # Add BGP Peering information
                    bgppeer = ip_node_name
                    self.d_addBGP(item, ipkey, bgppeer)
        return switch1
        
    def d_addBGP(self, item, ipkey, bgppeer):
        """Add BGP into the network diagram"""
        if not item.get('Site', None):
            return
        if not self.instance:
            return
        for intitem in self.instance.get('intents', []):
            for connections in intitem.get('json', {}).get('data', {}).get('connections', []):
                for terminal in connections.get('terminals', []):
                    if 'uri' not in terminal:
                        continue
                    if item['Site'] == terminal['uri'] and terminal.get(f'{ipkey.lower()}_prefix_list', None):
                        val = terminal[f'{ipkey.lower()}_prefix_list']
                        bgp_node_name = f"{bgppeer}_bgp{ipkey}"
                        bgp_node_label = f"BGP_{ipkey}"
                        bgp_node = Custom(bgp_node_label, self.SWITCH_ICON_PATH)
                        self.objects[bgp_node_name] = {"obj": bgp_node, "data": {}}
                        self.d_addLink(self.objects[bgppeer], self.objects[bgp_node_name], bgppeer, bgp_node_name)
                        peer_node_name = f"{bgppeer}_bgp{ipkey}_peer"
                        peer_node_label = val
                        peer_node = Custom(peer_node_label, self.SWITCH_ICON_PATH)
                        self.objects[peer_node_name] = {"obj": peer_node, "data": {}}
                        self.d_addLink(self.objects[bgp_node_name], self.objects[peer_node_name], bgp_node_name, peer_node_name)


    def addItem(self, item):
        """
        Add an item (host or switch) to the diagram by identifying its type and location (cluster).

        :param item: Dictionary containing item details.
        :return: Diagram object representing the item.
        """
        site = self.identifySite(item)
        if item['Type'] == 'Host':
            with Cluster(site):
                return self.d_addHost(item)
        elif item['Type'] == 'Switch':
            with Cluster(site):
                return self.d_addSwitch(item)

    def identifySite(self, item):
        """
        Identify the site or cluster to which the item (host or switch) belongs.

        :param item: Dictionary containing item details.
        :return: The name of the site or cluster.
        """
        site = None
        if item['Type'] == 'Host':
            site = item['Name'].split(':')[0]
        elif item['Type'] == 'Switch':
            site = item['Node'].split(':')[0]
        return site

    def setreverse(self, item):
        """
        Set the reverse flag for alternating between the first and last items in the input list.

        :param item: Dictionary containing item details.
        """
        if item['Type'] == 'Host' and self.popreverse is None:
            self.popreverse = False
        elif item['Type'] == 'Host' and self.popreverse is False:
            self.popreverse = True
        elif item['Type'] == 'Host' and self.popreverse is True:
            self.popreverse = False

    def createGraph(self, output_filename):
        """
        Create the network topology diagram and save it to a file.

        :param output_filename: Path where the output diagram will be saved.
        """
        output_dir = os.path.dirname(output_filename)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with Diagram("Network Topology", show=False, filename=output_filename):
            while len(self.indata) > 0:
                if self.popreverse in (None, False):
                    item = self.indata.pop(0)
                elif self.popreverse == True:
                    item = self.indata.pop()
                self.addItem(item)
                self.setreverse(item)
            self.d_addLinks()
