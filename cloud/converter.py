import json
import sys
import re 
import os
from datetime import datetime
import yaml
import time

def converter(data, id, name):
    # Loading in config_cloud/config.yml
    with open("../config_cloud/config.yml", 'r') as f:
        cloudConfig = yaml.safe_load(f)

    ports = data['Ports']

    flows = {}
    # Build unknown flow bucket for those with no flowID
    flows["unknown"] = []

    # Identify flows in SENSE-O Metadata Manifest
    for port in ports:
        if "Flow" in port:
            if port["Flow"] in flows.keys():
                flows[port["Flow"]].append(port)
            else:
                flows[port["Flow"]] = []
                flows[port["Flow"]].append(port)
        else:
            flows["unknown"].append(port)

    # Per-flow SENSE-RTMON config translation
    for flow in flows.keys():

        if (not flow == "unknown") or (flow == "unknown" and not len(flows["unknown"]) == 0):

            visitedPorts = []
            hostPeers = []
            switchPeers = []
            
            # output filename
            
            outFile = open("../config_flow/flow.yaml", "w")

            # User generated configs not available from SENSE Orchestrator
            outFile.write("## SECTION 1 GENERAL INFORMATION ##\n")


            # Flow information
            uuidStr = "rtmon-" + id + '\n'
            uuidConfig = "flow: \"" + uuidStr + "\"\n"
            outFile.write(uuidConfig)


            # title
            outFile.write(f"title: {name} \n")

            # writing Grafana configs from cloud/config.yml
            grafanaConfig = "grafana_host: \"" + str(cloudConfig['grafana_host']) + "\"\n"
            outFile.write(grafanaConfig)

            pushgatewayConfig = "pushgateway: \"" + str(cloudConfig['pushgateway']) + "\"\n"
            outFile.write(pushgatewayConfig)


            outFile.write("grafana_api_token: \n\n")

            # outFile.write("hostname:  \n")
            # outFile.write("sitename: \n")

           
            # Dynamically generated node data from SENSE Orchestrator JSON

            outFile.write("## Section 2 Hosts & Switches all under nodes ##\n")
            outFile.write("node:\n")

            # Per-flow translate to SENSE-RTMON system-specific config
            for port in flows[flow]:

                if "Host" in port:

                    hostInfo =   [port['Host'][0]["Name"], port['Host'][0]["Interface"], port['Vlan']]
                    switchPeers.append(port['Node'])
                    hostPeers.append(hostInfo)

                    outFile.write("  - name: \"")
                    outFile.write(port['Host'][0]["Name"])
                    outFile.write("\"\n")

                    outFile.write("    type: \"host\"\n")
                    # default is arp=on, runtime = 610 seconds
                    outFile.write("    arp: 'on'\n")
                    outFile.write("    runtime: 610\n")
                    outFile.write("    interface:\n")

                    for iface in port['Host']:
                        if "Interface" in iface:
                            if not iface["Interface"].startswith("?"):
                                outFile.write("      - name: \"")
                                outFile.write(iface['Interface'])
                                outFile.write("\"\n")
                            else:
                                outFile.write("      - name: \n")
                        else:
                            outFile.write("      - name: \n")

                        if "Vlan" in iface:
                            outFile.write("        vlan: ")
                            outFile.write(iface['Vlan'])
                            outFile.write("\n")
                        else: 
                            outFile.write("        vlan: 'not used'\n")

                        if "IPv4" in iface:
                            outFile.write("        ip: ")
                            outFile.write(iface['IPv4'].split("/")[0])
                            outFile.write("\n")

                        # outFile.write("        ping: \n")

                    outFile.write("      - name: \"")
                    outFile.write(port['Node'])
                    outFile.write("\"\n")

                    if "Vlan" in port:
                        outFile.write("        vlan: ")
                        outFile.write(port['Vlan'])
                        outFile.write("\n")
                    else: 
                        outFile.write("        vlan: 'not used'\n")	

                    outFile.write("        peer: \n")
                    if "Peer" in port:
                        if not port["Peer"].startswith("?"):
                            outFile.write("        - name: ")
                            outFile.write(port['Peer'])
                            outFile.write("\n")

                        else: 
                            outFile.write("        - name: \n")
                    else: 
                        outFile.write("        - name: \n")

                    if "Interface" in port:
                        outFile.write("          interface: ")
                        outFile.write(port["Interface"])
                        outFile.write("\n")
                    else: 
                        outFile.write("          interface: \n")

                    if "Vlan" in port:
                        outFile.write("          vlan: ")
                        outFile.write(port["Vlan"])
                        outFile.write("\n")
                    else: 
                        outFile.write("          vlan: 'not used'\n")



                    outFile.write("\n")
                    
            for port in ports:

                if port['Node'] not in visitedPorts:
                    outFile.write("  - name: \"")
                    currentNode = port['Node']
                    outFile.write(port['Node'])
                    outFile.write("\"\n")

                    outFile.write("    type: \"switch\"\n")
                    outFile.write("    runtime: 610\n")
                    outFile.write("    interface:\n")

                    for p in ports:
                        if p["Node"] == currentNode:

                            outFile.write("      - name: \"")
                            outFile.write(p['Port'].split(":")[-1])
                            outFile.write("\"\n")

                            if "Vlan" in p:
                                outFile.write("        vlan: ")
                                outFile.write(p["Vlan"])
                                outFile.write("\n")
                            else:
                                outFile.write("        vlan: 'not used'\n")

                            outFile.write("        peer:\n")
                            if "Peer" in p:
                                if not p["Peer"].startswith("?"):
                                    outFile.write("        - name: \"")
                                    outFile.write(p["Peer"].split(":")[-2])
                                    outFile.write("\"\n")

                                    outFile.write("          interface: \"")
                                    outFile.write(p["Peer"].split(":")[-1])
                                    outFile.write("\"\n")

                                    outFile.write("          vlan: 'not_used'\n")
                                elif p["Node"] in switchPeers:
                                    loc = switchPeers.index(p["Node"])
                                    peerName = "" if hostPeers[loc][0].startswith("?") else hostPeers[loc][0]
                                    peerIface = "" if hostPeers[loc][1].startswith("?") else "\"" +  hostPeers[loc][1] + "\""
                                    peerVlan = "" if hostPeers[loc][2].startswith("?") else hostPeers[loc][2]

                                    outFile.write("        - name: \"")
                                    outFile.write(peerName)
                                    outFile.write("\"\n")

                                    outFile.write("          interface: ")
                                    outFile.write(peerIface)
                                    outFile.write("\n")

                                    outFile.write("          vlan: ")
                                    outFile.write(peerVlan)
                                    outFile.write("\n")

                                else:
                                    outFile.write("        - name: \n")
                                    outFile.write("          interface: \n")
                                    outFile.write("          vlan: \n")	
                            else:
                                outFile.write("        - name: \n")
                                outFile.write("          interface: \n")
                                outFile.write("          vlan: \n")

                            outFile.write("\n")
                    outFile.write("\n")
                    visitedPorts.append(port['Node'])
                    #print("Finished parsing switch (", port['Node'],") info...\n")

            outFile.close()

    data = {}
    # Open and load YAML file
    with open("../config_flow/flow.yaml", 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print("error opening the file")
    
    #os.remove("test.yaml")
    
    return data
