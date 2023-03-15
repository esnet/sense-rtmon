import json
import os
import uuid
import sys


def orchestratorConvert(orchestrator_fname):
	f = open(orchestrator_fname)
	data = json.load(f)
	print("Loaded JSON data...")
	print("Parsing JSON data...\n")

	# output filename
	ofname = "sampleConverted.yaml"
	outFile = open(ofname, "w")

	# User generated configs not available from SENSE Orchestrator
	outFile.write("## SECTION 1 GENERAL INFORMATION ##\n")
	outFile.write("title: \n")
	outFile.write("flow: \n")

	uuidStr = str(uuid.uuid4())
	uuidConfig = "flow_uuid: \"" + uuidStr + "\"\n"
	outFile.write(uuidConfig)

	outFile.write("host_ip: \n")
	outFile.write("grafana_host: \n")
	outFile.write("pushgateway: \n")
	outFile.write("grafana_api_token: \n\n")

	print("---------------------------------")
	print("Writing User Generated Configs...")
	print("---------------------------------\n")
	# Dynamically generated node data from SENSE Orchestrator JSON

	outFile.write("## Section 2 Hosts & Switches all under nodes ##\n")
	outFile.write("node:\n")

	ports = data['Ports']
	visitedPorts = []

	for port in ports:

		if "Host" in port:
			print("Found host (", port['Host'][0]["Name"] ,") info in SENSE-Orchestrator Config!")
			print("Parsing host (", port['Host'][0]["Name"] ,") info...")
			outFile.write("  - name: \"")
			outFile.write(port['Host'][0]["Name"])
			outFile.write("\"\n")

			outFile.write("    type: \"host\"\n")
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

				if "IP Address" in iface:
					outFile.write("        ip: ")
					outFile.write(iface['IP Address'].split("/")[0])
					outFile.write("\n")

				outFile.write("        ping: \n")

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

		if port['Node'] not in visitedPorts:
			print("Found switch (", port['Node'],") info in SENSE-Orchestrator Config!")
			print("Parsing switch (", port['Node'],") info...")
			outFile.write("  - name: \"")
			currentNode = port['Node']
			outFile.write(port['Node'])
			outFile.write("\"\n")

			outFile.write("    type: \"switch\"\n")
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

	with open('sampleConverted.yaml', 'r') as readF:
		print(readF.read())

try:
	configName = sys.argv[1]
	print("Found JSON file from SENSE-Orchestrator...")
	orchestratorConvert(configName)
	print("Finished building SENSE-RTMON Config!\n")
except IndexError:
	print("Usage Error: Please specify an orchestrator config file!")
