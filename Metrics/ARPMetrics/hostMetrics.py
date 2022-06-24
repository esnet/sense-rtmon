#!/usr/bin/env python3

import sys
import subprocess
from subprocess import Popen
import json
import yaml
import os

try:
    # Load yaml config file as dict
    owd = os.getcwd()
    os.chdir("etc")
    os.chdir("arp_exporter")
    infpth = str(os.path.abspath(os.curdir)) + "/arp.yml"
    os.chdir(owd)
    data = {}
    with open(infpth, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print("Config file load error!")

    subprocess.run("mkdir arpFiles", shell=True)
    subprocess.run("mkdir jsonFiles", shell=True)

    arpCMDs = []

    arpCollect = "count=1; end=$((SECONDS+" + str(data['arpMetrics']['scrapeDuration']) + ")); while [ $SECONDS -lt $end ]; do sleep " + str(data['arpMetrics']['scrapeInterval']) +"; arp -a > ./arpFiles/arpOut-$count.txt;  python3 convertARP.py ./arpFiles/arpOut-$count.txt ./jsonFiles/arpOut-$count.json; done"
    arpCMDs.append(arpCollect)
    # run in parallel
    processes = [Popen(cmd, shell=True) for cmd in arpCMDs]
    for p in processes: p.wait()
except KeyboardInterrupt:
    subprocess.run("rm -R arpFiles", shell=True)
    subprocess.run("rm -R jsonFiles", shell=True)
