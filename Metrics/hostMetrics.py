#!/usr/bin/env python3

import sys
import subprocess
import json
import yaml

# Load yaml config file as dict
data = {}
with open(sys.argv[1], 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("Config file load error!")

tcpdumpCMDs = []
tcpdumpCMDs.append("tcpdump -G " + str(data['scrapeDuration']) + " -W 1 -i" + data['hostA']['interfaceName'] + " -s 100 host " + data['hostA']['IP'] +" -nA -w tcpdumpA.pcap")
tcpdumpCMDs.append("tcpdump -G " + str(data['scrapeDuration']) + " -W 1 -i" + data['hostB']['interfaceName'] + " -s 100 host " + data['hostB']['IP'] +" -nA -w tcpdumpB.pcap")

for cmd in tcpdumpCMDs:
    subprocess.run(cmd, shell=True)

subprocess.run("tshark -r tcpdumpA.pcap -T json >tcpdumpA.json", shell=True)
subprocess.run("tshark -r tcpdumpB.pcap -T json >tcpdumpB.json", shell=True)

subprocess.run("arp -a > arpOut.txt", shell=True)

subprocess.run("python3 convertARP.py arpOut.txt", shell=True)
