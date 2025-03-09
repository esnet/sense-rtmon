"""
DiagramWorker Class for Network Topology Visualization

This module contains the DiagramWorker class, which generates network topology diagrams 
by processing input data that includes hosts and switches. It uses the 'diagrams' library 
to visualize network components and their interconnections.
"""
import os
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from diagrams.generic.compute import Rack
from diagrams.aws.compute import Batch as dSwitch
#from RTMonLibs.GeneralLibs import _processName
# change later:
def _processName(name):
    """Process Name for Mermaid and replace all special chars with _"""
    for repl in [[" ", "_"], [":", "_"], ["/", "_"], ["-", "_"], [".", "_"], ["?", "_"]]:
        name = name.replace(repl[0], repl[1])
    return name
#########

class DiagramWorker:
    """
    DiagramWorker class is responsible for generating network topology diagrams
    using the input data that contains host and switch information. The class
    identifies and visualizes links between network components.
    """
    HOST_ICON_PATH = '/opt/icons/host.png'
    SWITCH_ICON_PATH = '/opt/icons/switch.png'
    BGP_ICON_PATH = '/opt/icons/BGP.png'
    MUL_ICON_PATH = '/opt/icons/multipoint.png'
    # TEmp
    # HOST_ICON_PATH = '/Users/sunami/Desktop/publish/sense-rtmon/autogole-api/packaging/icons/host.png'
    # SWITCH_ICON_PATH = '/Users/sunami/Desktop/publish/sense-rtmon/autogole-api/packaging/icons/switch.png'
    # BGP_ICON_PATH  = '/Users/sunami/Desktop/publish/sense-rtmon/autogole-api/packaging/icons/BGP.png'
    def __init__(self, instance):
        """
        Initialize the DiagramWorker with input data.

        :param indata: List of dictionaries containing host and switch details.
        """
        self.objects = {}
        self.added = {}
        self.linksadded = set()
        self.popreverse = None
        self.instance = instance
        self.unique = {}

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

            val1["obj"] >> Edge(label=self.d_LinkLabel(val1, val2)) << val2["obj"]  # pylint: disable=expression-not-assigned

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
                    ## if Peer to host pair not found for overide
                    else:
                        try:
                            siteName, switchName = self.objects[vals['data']['Peer']]['data']["Node"].split(":")
                            portname = self.objects[vals['data']['Peer']]['data']["Name"]
                        except:
                            siteName, switchName, portname = vals['data']['Peer'], vals['data']['Peer'], "Unknown"
                        with Cluster(siteName):
                            newSwitch = Custom(switchName, self.SWITCH_ICON_PATH)
                        newSwitch >> Edge(label="Port 1: " + portname + '\n' + "Port 2: "+ vals['data']["Name"] + '\n' + "Vlan: " +  vals['data']["Vlan"]) << vals["obj"]  # pylint: disable=expression-not-assigned
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
            return None
        switchLabel = item['Node'].split(":")[1]
        switchLabel += ("\nIPv4: " + item["IPv4"]) if item["IPv4"] != '?port_ipv4?' else ""
        switchLabel += ("\nIPv6: " + item["IPv6"]) if item["IPv6"] != '?port_ipv6?' else ""
        if switchLabel in self.unique:
            edge=""
            if item["Peer"] == "?peer?":
                edge = "Port1: " + item['Name']
                edge += "\nVlan: " + item["Vlan"]
            else:
                edge = "Port1: " + self.unique[switchLabel][1]['Name']
                edge += "\nVlan: " + self.unique[switchLabel][1]["Vlan"]

            ds = Custom("PORT", self.MUL_ICON_PATH)
            ds  >> Edge(label= edge, minlen="1") << self.unique[switchLabel][0]
            switch1 = self.unique[switchLabel][0]
        else:
            switch1 = Custom(switchLabel, self.SWITCH_ICON_PATH)
            self.unique[switchLabel] = [switch1, item]
        if 'Peer' in item and item['Peer'] != "?peer?":
            self.added[item['Node']] = item['Port']
            self.objects[item['Port']] = {"obj": switch1, "data": item}
        elif 'PeerHost' in item:
            uniqname = _processName(f'{item["Node"]}_{item["Name"]}')
            self.added[item['Node']] = uniqname
            self.objects[uniqname] = {"obj": switch1, "data": item}
        # Add IPv4/IPv6 on the switch
        #BGP
        with Cluster("BGP Peering", graph_attr={"label": "BGP Peering", "style": "dotted", "color": "black", "rankdir": "TB", "nodesep": "0.5", "ranksep": "0.4"}):
            for ipkey, ipdef in {'IPv4': '?port_ipv4?', 'IPv6': '?port_ipv6?'}.items():
                if ipkey in item and item[ipkey] != ipdef:
                    ipLabel = item[ipkey]
                    ipLabel2 = None
                    sitename = item.get("Site")
                    if self.instance is not None:
                        for flow in self.instance.get("intents", []):
                            for connections in flow.get('json', {}).get('data', {}).get('connections', []):
                                for terminal in connections.get('terminals', []):
                                    if "uri" not in terminal:
                                        continue
                                    if terminal["uri"] == sitename and terminal.get(f'{ipkey.lower()}_prefix_list'):
                                        ipLabel2 = terminal[f'{ipkey.lower()}_prefix_list']
                                        break
                                if ipLabel2:
                                    break
                            if ipLabel2:
                                break
                    if ipLabel2:
                        ipNode = Custom("NeighIP: " + ipLabel + '\n' + "RouteMap: " + ipLabel2, self.BGP_ICON_PATH)
                        switch1 >> Edge(minlen="1") << ipNode  # pylint: disable=expression-not-assigned
                        break
        return switch1

    def d_addItem(self, item):
        """
        Add an item (host or switch) to the diagram by identifying its type and location (cluster).

        :param item: Dictionary containing item details.
        :return: Diagram object representing the item.
        """
        site = self.d_identifySite(item)
        if item['Type'] == 'Host':
            with Cluster(site):
                self.d_addHost(item)
        elif item['Type'] == 'Switch':
            with Cluster(site):
                self.d_addSwitch(item)

    def d_identifySite(self, item):
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

    def d_setreverse(self, item):
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


    def createGraph(self, output_filename, indata):
        """
        Create the network topology diagram and save it to a file.

        :param output_filename: Path where the output diagram will be saved.
        """
        outputDir = os.path.dirname(output_filename)
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        with Diagram("Network Topology", show=False, filename=output_filename):
            item = None
            while len(indata) > 0:
                if self.popreverse in (None, False):
                    item =indata.pop(0)
                elif self.popreverse is True:
                    item = indata.pop()
                self.d_addItem(item)
                self.d_setreverse(item)
            self.d_addLinks()
