#!/usr/bin/env python3

import yaml
import sys
import fileinput
import subprocess
import os
from datetime import datetime

# Help Command
if len(sys.argv) <= 1 or str(sys.argv[1]) == "-h" or str(sys.argv[1]) == "-H":
        print("\n USAGE: python3 dynamic.py <config-file> \n \n Tip: Ensure that the Python script dynamic.py, the supporting files, and the config file are in one directory without subdirectories or other hierarchies.\n")
else: 
    try:
        print("Starting script...")
        # Load yaml config file as dict
        print("Parsing config file...")
        data = {}
        with open(sys.argv[1], 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print("\n USAGE: python3 dynamic.py <config-file> \n \n Tip: Ensure that the Python script dynamic.py, the supporting files, and the config file are in one directory without subdirectories or other hierarchies.\n")
        print("Collecting SNMP generator template...")
        with open('generatorTemplate.yml') as inGen, open('generator.yml', 'w') as outGen:
             for line in inGen:
                 outGen.write(line)
        print("Reading SNMP OIDs/Interfaces/Scrape Duration/Scrape Time from config file...")
        oids = set(data['oids'])
        for i in range(len(oids)):
            oid = next(iter(oids))
            snip = "      - " + str(oid) + "\n"
            with open('generator.yml', 'r') as gen:
                text = gen.readlines()
            text[3+i] = snip
            with open('generator.yml', 'w') as genOut:
                genOut.writelines(text)
            oids.remove(oid)
        replacements = {'RETRY': str(data['retries']),
                        'TIMEOUT': str(data['scrapeTimeout']),
                        'COMMUNITYREADSTRING': str(data['communityString'])}
         # Iteratively find and replace in one go 
       # Read in the file
        with open('generator.yml', 'r') as file:
            filedata = file.read()
        # Replace the target string
        for k,v in replacements.items():
            filedata = filedata.replace(k, v)
        # Write the file out again
        print("Writing SNMP Exporter generator config file...")
        with open('generator.yml', 'w') as file:
            file.write(filedata)
        print("Configuring SNMP Exporter Generator...")
        subprocess.run("sudo yum -y install gcc gcc-c++ make net-snmp net-snmp-utils net-snmp-libs net-snmp-devel", shell=True)
        subprocess.run("wget https://dl.google.com/go/go1.13.linux-amd64.tar.gz", shell=True)
        subprocess.run("sudo tar -C /usr/local -xzf go1.13.linux-amd64.tar.gz", shell=True)
        #subprocess.run("export PATH=$PATH:/usr/local/go/bin", shell=True)
        os.environ["PATH"] += os.pathsep + os.pathsep.join(["/usr/local/go/bin"])
        dir = str(os.getcwd())
        os.putenv("GOPATH", dir)
        subprocess.run("go get github.com/prometheus/snmp_exporter/generator", shell=True)
        genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
        genCmd = "sudo mv generator.yml " + genLoc
        subprocess.run(genCmd, shell=True)
        subprocess.run("go build", shell=True, cwd=genLoc)
        subprocess.run("make mibs", shell=True, cwd=genLoc)
        print("Generating dynamic SNMP config file...")
        subprocess.run("./generator generate", shell=True, cwd=genLoc)
        print("Initializing docker container with custom SNMP exporter...")
        subprocess.run("sudo docker run -d --name snmp-exporter -p 9116:9116     -v $PWD/snmp.yml:/etc/snmp_exporter/snmp.yml prom/snmp-exporter", shell=True, cwd=genLoc)
        print("Success! Configured custom SNMP Exporter container")
    except KeyboardInterrupt:
        print("Interrupt detected")
        subprocess.run("sudo docker stop snmp-exporter", shell=True)
        print("Shutting down SNMP Exporter instance to save resources...")
