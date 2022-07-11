import yaml
import sys
import fileinput
import subprocess
import os
from datetime import datetime

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

# read all oids in first then add to generator file
snip = ""
for oid in oids:
    snip = snip + "      - " + str(oid) + "\n"
    # oids.remove(oid)
with open('generator.yml', 'r') as gen:
        text = gen.readlines()
text[3] = snip
with open('generator.yml', 'w') as genOut:
    genOut.writelines(text)
    
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
dir = str(os.getcwd())
subprocess.run("./generator generate", shell=True, cwd=dir)
print("Success! Configured custom SNMP Exporter container")
