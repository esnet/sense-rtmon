import copy
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EC2
from diagrams.aws.network import Route53
from diagrams.generic.network import Switch
from diagrams.oci.compute import ContainerWhite
from diagrams.generic.compute import Rack
from diagrams.generic.blank import Blank
from diagrams.aws.compute import EC2ElasticIpAddress
from diagrams.aws.iot import IotAnalyticsChannel



from diagrams.aws.compute import EC2ElasticIpAddress as dIP
from diagrams.aws.compute import ElasticContainerServiceContainer as dServer
from diagrams.aws.compute import EC2Instance as dInterface
from diagrams.aws.compute import EC2AutoScaling as dVlan
from diagrams.aws.compute import Batch as dSwitch


#{T3_US_Starlight:r740xd4.it.northwestern.edu: [{linkto: T3_US_Starlight:s1, obj: obj}]
#T3_US_Starlight:s1: [{linkto: T3_US_Starlight:r740xd4.it.northwestern.edu, obj: obj},
#                     {linkto: urn:ogf:network:icair.org:2013:mren8700:r740xd4, obj: obj}],

indata = [{'IPv4': '?ipv4?',
  'IPv6': 'fc00:3986:0:0:0:0:1:ecb0/128',
  'Interface': 'eno1',
  'Link': 'T3_US_Starlight:s1',
  'MAC': '24:6e:96:5b:bf:58',
  'Name': 'T3_US_Starlight:r740xd4.it.northwestern.edu',
  'Type': 'Host',
  'Vlan': '1381'},
 {'Name': '12',
  'Node': 'T3_US_Starlight:s1',
  'Peer': '?peer?',
  'PeerHost': 'T3_US_Starlight:r740xd4.it.northwestern.edu',
  'Port': 'urn:ogf:network:starlight.org:2022:s1:1_2',
  'Site': 'urn:ogf:network:starlight.org:2022',
  'Type': 'Switch',
  'Vlan': '1381'},
 {'Name': '11',
  'Node': 'T3_US_Starlight:s1',
  'Peer': 'urn:ogf:network:icair.org:2013:mren8700:r740xd4',
  'Port': 'urn:ogf:network:starlight.org:2022:s1:1_1',
  'Site': 'urn:ogf:network:starlight.org:2022',
  'Type': 'Switch',
  'Vlan': '1381'},
 {'Name': 'r740xd4',
  'Node': 'NSI_STARLIGHT:mren8700',
  'Peer': 'urn:ogf:network:starlight.org:2022:s1:1_1',
  'Port': 'urn:ogf:network:icair.org:2013:mren8700:r740xd4',
  'Site': 'urn:ogf:network:icair.org:2013:mren8700',
  'Type': 'Switch',
  'Vlan': '1381'},
 {'Name': 'esnet',
  'Node': 'NSI_STARLIGHT:mren8700',
  'Peer': 'urn:ogf:network:es.net:2013::star-cr6:2_1_c5_1:+',
  'Port': 'urn:ogf:network:icair.org:2013:mren8700:esnet',
  'Site': 'urn:ogf:network:icair.org:2013:mren8700',
  'Type': 'Switch',
  'Vlan': '1789'},
 {'JointNetwork': 'star-cr6|2_1_c5_1',
  'JointSite': 'ESnet',
  'Name': '2_1_c5_1',
  'Node': 'ESnet:star-cr6',
  'Peer': 'urn:ogf:network:icair.org:2013:mren8700:esnet',
  'Port': 'urn:ogf:network:es.net:2013::star-cr6:2_1_c5_1:+',
  'Site': 'urn:ogf:network:es.net:2013:',
  'Type': 'Switch',
  'Vlan': '1789'},
 {'IPv4': '?ipv4?',
  'IPv6': 'fc00:3986:0:0:0:0:1:ecaf/128',
  'Interface': 'enp1s0',
  'Link': 'T2_US_UMD_s0_12',
  'MAC': '52:54:00:0e:7e:ee',
  'Name': 'T2_US_UMD:ptxn-sense-v1.maxgigapop.net',
  'Type': 'Host',
  'Vlan': '3608'},
 {'Name': '12',
  'Node': 'T2_US_UMD:s0',
  'Peer': '?peer?',
  'PeerHost': 'T2_US_UMD:ptxn-sense-v1.maxgigapop.net',
  'Port': 'urn:ogf:network:maxgigapop.net:2013:s0:1_2',
  'Site': 'urn:ogf:network:maxgigapop.net:2013',
  'Type': 'Switch',
  'Vlan': '3608'},
 {'Name': '11',
  'Node': 'T2_US_UMD:s0',
  'Peer': 'urn:ogf:network:es.net:2013::wash-cr6:lag-50:wix',
  'Port': 'urn:ogf:network:maxgigapop.net:2013:s0:1_1',
  'Site': 'urn:ogf:network:maxgigapop.net:2013',
  'Type': 'Switch',
  'Vlan': '3608'},
 {'JointNetwork': 'wash-cr6|lag-50|wix',
  'JointSite': 'ESnet',
  'Name': 'wix',
  'Node': 'ESnet:wash-cr6',
  'Peer': 'urn:ogf:network:maxgigapop.net:2013:s0:1_1',
  'Port': 'urn:ogf:network:es.net:2013::wash-cr6:lag-50:wix',
  'Site': 'urn:ogf:network:es.net:2013:',
  'Type': 'Switch',
  'Vlan': '3608'},
 {'JointNetwork': 'newy32aoa-cr6|1_1_c13_1|fabric',
  'JointSite': 'ESnet',
  'Name': 'fabric',
  'Node': 'ESnet:newy32aoa-cr6',
  'Peer': 'urn:ogf:network:stack-fabric:2024:topology:node+NEWY:port+ESnet-400G-NEWY',
  'Port': 'urn:ogf:network:es.net:2013::newy32aoa-cr6:1_1_c13_1:fabric',
  'Site': 'urn:ogf:network:es.net:2013:',
  'Type': 'Switch',
  'Vlan': '2038'},
 {'JointNetwork': 'topology|node+NEWY|port+ESnet-400G-NEWY',
  'JointSite': 'NSI_FABRIC',
  'Name': 'port+ESnet-400G-NEWY',
  'Node': 'NSI_FABRIC:topology',
  'Peer': 'urn:ogf:network:es.net:2013::newy32aoa-cr6:1_1_c13_1:fabric',
  'Port': 'urn:ogf:network:stack-fabric:2024:topology:node+NEWY:port+ESnet-400G-NEWY',
  'Site': 'urn:ogf:network:stack-fabric:2024:topology',
  'Type': 'Switch',
  'Vlan': '2038'},
 {'JointNetwork': 'topology|node+STAR|port+Internet2-StarLight',
  'JointSite': 'NSI_FABRIC',
  'Name': 'port+Internet2-StarLight',
  'Node': 'NSI_FABRIC:topology',
  'Peer': 'urn:ogf:network:al2s.internet2.edu:2023:node+core1.star:port+HundredGigE0_0_0_20',
  'Port': 'urn:ogf:network:stack-fabric:2024:topology:node+STAR:port+Internet2-StarLight',
  'Site': 'urn:ogf:network:stack-fabric:2024:topology',
  'Type': 'Switch',
  'Vlan': '3727'},
 {'JointNetwork': 'node+core1.star|port+HundredGigE0_0_0_20',
  'JointSite': 'Internet2',
  'Name': 'port+HundredGigE0_0_0_20',
  'Node': 'Internet2:node+core1.star',
  'Peer': 'urn:ogf:network:stack-fabric:2024:topology:node+STAR:port+Internet2-StarLight',
  'Port': 'urn:ogf:network:al2s.internet2.edu:2023:node+core1.star:port+HundredGigE0_0_0_20',
  'Site': 'urn:ogf:network:al2s.internet2.edu:2023',
  'Type': 'Switch',
  'Vlan': '3727'},
 {'JointNetwork': 'node+core2.sunn|port+HundredGigE0_0_0_24',
  'JointSite': 'Internet2',
  'Name': 'port+HundredGigE0_0_0_24',
  'Node': 'Internet2:node+core2.sunn',
  'Peer': 'urn:ogf:network:es.net:2013::sunn-cr6:1_1_c3_1:al2s',
  'Port': 'urn:ogf:network:al2s.internet2.edu:2023:node+core2.sunn:port+HundredGigE0_0_0_24',
  'Site': 'urn:ogf:network:al2s.internet2.edu:2023',
  'Type': 'Switch',
  'Vlan': '2403'},
 {'JointNetwork': 'sunn-cr6|1_1_c3_1|al2s',
  'JointSite': 'ESnet',
  'Name': 'al2s',
  'Node': 'ESnet:sunn-cr6',
  'Peer': 'urn:ogf:network:al2s.internet2.edu:2023:node+core2.sunn:port+HundredGigE0_0_0_24',
  'Port': 'urn:ogf:network:es.net:2013::sunn-cr6:1_1_c3_1:al2s',
  'Site': 'urn:ogf:network:es.net:2013:',
  'Type': 'Switch',
  'Vlan': '2403'}]

#from diagrams.aws.compute import EC2ElasticIpAddress as dIP
#from diagrams.aws.compute import ElasticContainerServiceContainer as dServer
##from diagrams.aws.compute import EC2Instance as dInterface
#from diagrams.aws.compute import EC2AutoScaling as dVlan
#from diagrams.aws.compute import Batch as dSwitch

def _processName(name):
    """Process Name for Mermaid and replace all special chars with _"""
    for repl in [[" ", "_"], [":", "_"], ["/", "_"], ["-", "_"], [".", "_"], ["?", "_"]]:
        name = name.replace(repl[0], repl[1])
    return name




class DiagramWorker():
    def __init__(self, indata):
        self.indata = indata
        self.objects = {}
        self.added = {}
        self.linksadded = []
        self.popreverse = None

    def _d_findItem(self, fval, fkey):
        """Find Item of fkey == fval"""
        for key, vals in self.objects.items():
            if vals.get('data', {}).get(fkey, '') == fval:
                return key, self.objects[key]
        return None

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
            if [key, fkey] in self.linksadded or [fkey, key] in self.linksadded:
                return
            self.linksadded.append([key, fkey])
            self.d_LinkLabel(val1, val2)
            import pdb; pdb.set_trace()
            val1["obj"] >> Edge(label=self.d_LinkLabel(val1, val2)) << val2["obj"]

    def d_addLinks(self):
        """Identify Links between items"""
        for key, vals in self.objects.items():
            if vals.get('data', {}).get('Type', '') == "Host":
                fKey, fItem = self._d_findItem(key, 'PeerHost')
                self.d_addLink(self.objects[key], fItem, key, fKey)
            elif vals.get('data', {}).get('Type', '') == "Switch":
                if 'Peer' in  vals.get('data', {}) and vals['data']['Peer'] != "?peer?":
                    fKey, fItem = self._d_findItem(vals['data']['Peer'], "Port")
                    self.d_addLink(self.objects[key], fItem, key, fKey)
                    print(vals)

    def d_addHost(self, item):
        """{'IPv4': '?ipv4?',
            'IPv6': 'fc00:3986:0:0:0:0:1:ecb0/128',
            'Interface': 'eno1',
            'Link': 'T3_US_Starlight_s1_12',
            'MAC': '24:6e:96:5b:bf:58',
            'Name': 'T3_US_Starlight:r740xd4.it.northwestern.edu',
            'Type': 'Host',
            'Vlan': '1381'}"""
        name = f"Host: {item['Name'].split(':')[1]}"
        name += f"\nInterface: {item['Interface']}"
        name += f"\nVlan: {item['Vlan']}"
        #worker = Rack(f"{item['Name'].split(':')[1]}:{item['Interface']}")
        #worker = Rack(name)
        #vlan = dVlan(f"vlan.{item['Vlan']}")
        if 'IPv4' in item and item['IPv4'] != "?ipv4?":
            name += f"\nIPv4: {item['IPv4']}"
            #ipv4 = dIP(item['IPv4'])
            #worker >> Edge(label=f"vlan.{item['Vlan']}") << ipv4
        if 'IPv6' in item and item['IPv4'] != "?ipv6?":
            name += f"\nIPv6: {item['IPv6']}"
            #ipv6 = dIP(item['IPv6'])
            #worker >> Edge(label=f"vlan.{item['Vlan']}") << ipv6
        worker = Rack(name)
        uniqname = _processName(f'{item["Name"]}_{item["Interface"]}')
        self.objects[item['Name']] = {"obj": worker, "data": item}
        return worker

    def d_addSwitch(self, item):
        """'JointNetwork': 'node+core1.star|port+HundredGigE0_0_0_20',
  'JointSite': 'Internet2',
  'Name': 'port+HundredGigE0_0_0_20',
  'Node': 'Internet2:node+core1.star',
  'Peer': 'urn:ogf:network:stack-fabric:2024:topology:node+STAR:port+Internet2-StarLight',
  'Port': 'urn:ogf:network:al2s.internet2.edu:2023:node+core1.star:port+HundredGigE0_0_0_20',
  'Site': 'urn:ogf:network:al2s.internet2.edu:2023',
  'Type': 'Switch',
  'Vlan': '3727'"""
        if item['Node'] in self.added:
            uniqname = _processName(f'{item["Node"]}_{item["Name"]}')
            self.objects[uniqname] = {"obj": self.objects[self.added[item['Node']]]["obj"], "data": item}
            return
        switch1 = dSwitch(item['Node'].split(":")[1])
        uniqname = _processName(f'{item["Node"]}_{item["Name"]}')
        if 'Peer' in item and item['Peer'] != "?peer?":
            self.added[item['Node']] = item['Port']
            self.objects[item['Port']] = {"obj": switch1, "data": item}
            #if item['Peer'] in self.objects:
            #    self.objects[item['Peer']] >> switch1
            #    del self.objects[item['Peer']]
        elif 'PeerHost' in item:
            uniqname = _processName(f'{item["Node"]}_{item["Name"]}')
            self.added[item['Node']] = uniqname
            self.objects[uniqname] = {"obj": switch1, "data": item}
        #if 'PeerHost' in item and item['PeerHost'] in self.objects:
        #    self.objects[item['PeerHost']] >> switch1 
        #    del self.objects[item['PeerHost']]
        return switch1

    def addItem(self, item):
        """Add Item"""
        site = self.identifySite(item)
        if item['Type'] == 'Host':
            with Cluster(site):
                return self.d_addHost(item)
        elif item['Type'] == 'Switch':
            with Cluster(site):
                return self.d_addSwitch(item)

    def identifySite(self, item):
        site = None
        if item['Type'] == 'Host':
            site = item['Name'].split(':')[0]
        elif item['Type'] == 'Switch':
            site = item['Node'].split(':')[0]
        return site

    def setreverse(self, item):
        if item['Type'] == 'Host' and self.popreverse == None:
            self.popreverse = False
        elif item['Type'] == 'Host' and self.popreverse == False:
            self.popreverse = True
        elif item['Type'] == 'Host' and self.popreverse == True:
            self.popreverse = False

    def createGraph(self):
        with Diagram("Grouped Workers", show=False):
            while len(self.indata) > 0:
                if self.popreverse == None or self.popreverse == False:
                    item = self.indata.pop(0)
                elif self.popreverse == True:
                    print('REVERSE')
                    item = self.indata.pop()
                self.addItem(item)
                self.setreverse(item)
            # Need to add links
            self.d_addLinks()
            print(self.objects)


workers = {}
# Create the diagram
ww = DiagramWorker(indata)
ww.createGraph()
#with Diagram("Grouped Workers", show=False, direction="TB"):
#    ww.createGraph()
    # Optionally use a cluster to group the workers
    # 0. While len > 0
    # 1. Pop first item from the list
    #    a. Call addItem
        # if Type "Host" - take Name and split : 0 - Sitename;
        #     Add all host information
        # if Type "Switch" - take Node - and split : 0 - Sitename;
        # Identify all the remaining ones for specific site and return (which starts with sitename)
    # If return remaining - for each - call addItem
    #with Cluster("Worker Cluster"):
    #    for name in worker_names:
    #        worker = EC2(name)
    #        workers[name] = worker
    #dns = Route53("dns")
    #for workname, worker in workers.items():
    #    dns >> worker
