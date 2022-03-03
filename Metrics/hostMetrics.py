#!/usr/bin/env python3

import sys
import subprocess
from subprocess import Popen
import json
import yaml

try:
    # Load yaml config file as dict
    data = {}
    with open(sys.argv[1], 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print("Config file load error!")

    subprocess.run("mkdir tcpFiles", shell=True)
    subprocess.run("mkdir jsonFiles", shell=True)

    tcpdumpCMDs = []
    tcpdumpCMDs.append("tcpdump -i " + str(data['hostA']['interfaceName']) + " -w tcpFiles/trace-%y-%m-%d-%H-%M-%S.pcap -W " + str(data['scrapeDuration']) + " -G 1 -s96 -nA -Z root")

    # Defaults to selecting the most recent 1 second's data from the most recent .pcap file
    if data['continuousCollect']:
        jsonConvert = "cd tcpFiles; count=1; end=$((SECONDS+" + str(data['scrapeDuration']) + ")); while [ $SECONDS -lt $end ]; do sleep " + str(data['scrapeInterval']) +"; mergecap -w merged-$count.pcap $(ls -t trace*.pcap | head -n" + str(data['scrapeDuration']) +"); for f in $(ls -t *.pcap | head -n1); do if [ ! -f ${f%.pcap}.json ]; then tshark -r $f -T json >../jsonFiles/${f%.pcap}.json; let count++; fi; done; done"
    else: 
        jsonConvert = "cd tcpFiles; end=$((SECONDS+" + str(data['scrapeDuration']) + ")); while [ $SECONDS -lt $end ]; do sleep " + str(data['scrapeInterval']) +"; for f in $(ls -t *.pcap | head -n1); do if [ ! -f ${f%.pcap}.json ]; then tshark -r $f -T json >../jsonFiles/${f%.pcap}.json; fi; done; done"
    
    tcpdumpCMDs.append(jsonConvert)

    # run in parallel
    processes = [Popen(cmd, shell=True) for cmd in tcpdumpCMDs]
    for p in processes: p.wait()
except KeyboardInterrupt:
    subprocess.run("rm -R tcpFiles", shell=True)
    subprocess.run("rm -R jsonFiles", shell=True)

# subprocess.run("arp -a > arpOut.txt", shell=True)

# subprocess.run("python3 convertARP.py arpOut.txt", shell=True)
