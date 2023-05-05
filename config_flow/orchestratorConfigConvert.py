import json
import os
import uuid
import yaml
import sys

from time import gmtime, strftime


def orchestratorConvert(orchestrator_fname):
	f = open(orchestrator_fname)
	data = json.load(f)
	print("Loaded JSON data...")
	print("Parsing JSON data...\n")

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
				print("---------------------------------")
				print("Detected new flow: flow ID = \'", port["Flow"] ,"\'...")
				print("---------------------------------\n")
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
			ofname = "auto_config/config_" + str(flow) + ".yaml"
			outFile = open(ofname, "w")

			# User generated configs not available from SENSE Orchestrator
			outFile.write("## SECTION 1 GENERAL INFORMATION ##\n")


			# Flow information
			flowStr = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
			uuidStr = "rtmon-" + str(flowStr)
			uuidConfig = "flow: \"" + uuidStr + "\"\n"
			outFile.write(uuidConfig)


			# title
			outFile.write("title: \"PlaceholderArbitraryTitle\" \n")

			# writing Grafana configs from cloud/config.yml
			grafanaConfig = "grafana_host: \"" + str(cloudConfig['grafana_host']) + "\"\n"
			outFile.write(grafanaConfig)

			pushgatewayConfig = "pushgateway: \"" + str(cloudConfig['pushgateway']) + "\"\n"
			outFile.write(pushgatewayConfig)


			outFile.write("grafana_api_token: \n\n")

			print("---------------------------------")
			print("Writing User Generated Configs: flow ID = \'", flow ,"\'...")
			print("---------------------------------\n")
			# Dynamically generated node data from SENSE Orchestrator JSON

			outFile.write("## Section 2 Hosts & Switches all under nodes ##\n")
			outFile.write("node:\n")

			# Per-flow translate to SENSE-RTMON system-specific config
			for port in flows[flow]:

				if "Host" in port:
					print("Found host (", port['Host'][0]["Name"] ,") info in SENSE-Orchestrator Config!")
					print("Parsing host (", port['Host'][0]["Name"] ,") info...")

					hostInfo = [port['Host'][0]["Name"], port['Host'][0]["Interface"], port['Vlan']]
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
					print("Finished parsing host (", port['Host'][0]["Name"] ,") info...\n")

			for port in ports:

				if port['Node'] not in visitedPorts:
					print("Found switch (", port['Node'],") info in SENSE-Orchestrator Config!")
					print("Parsing switch (", port['Node'],") info...")
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
					print("Finished parsing switch (", port['Node'],") info...\n")


			print("---------------------------------")
			print("Dynamically generating config data from SENSE-Orchestrator...")
			print("---------------------------------")

			outFile.close()

			with open(ofname, 'r') as readF:
				print(readF.read())


try:
	configName = sys.argv[1]
	print("Found JSON file from SENSE-Orchestrator...")
	orchestratorConvert(configName)
	print("Finished building SENSE-RTMON Config!\n")
except IndexError:
	print("Usage Error: Please specify an orchestrator config file!")
