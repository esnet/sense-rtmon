import yaml
import sys
import subprocess
import os

print("Starting script...")
# Load yaml config file as dict
print("Parsing config file...")
data = {}
with open(sys.argv[1], 'r') as stream:
    data = yaml.safe_load(stream)

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
genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
genCmd = "yes | cp -rfa generator.yml " + genLoc

print("Generating dynamic SNMP config file...")
subprocess.run("./generator generate", shell=True, cwd=genLoc)
subprocess.run("yes | cp -rfa snmp.yml ../../../../../", shell=True, cwd=genLoc)
print("Success! Configured custom SNMP Exporter container")
