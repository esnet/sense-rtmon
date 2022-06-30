import yaml
import sys
import fileinput
import subprocess
import os
from datetime import datetime

print("Parsing config file...")
# Load yaml config file as dict
owd = os.getcwd()
os.chdir("..")
infpth = str(os.path.abspath(os.curdir)) + "/config.yml"
os.chdir(owd)
data = {}
with open(infpth, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("\n Config file 'config.yml' could not be found in the DynamicDashboard directory\n")

print("Collecting SNMP generator template...")
with open('generatorTemplate.yml') as inGen, open('generator.yml', 'w') as outGen:
        for line in inGen:
            outGen.write(line)
print("Reading SNMP OIDs/Interfaces/Scrape Duration/Scrape Time from config file...")
oids = set(data['snmpMetrics']['oids'])

# read all oids in first then add to generator file
snip = ""
for oid in oids:
    snip = snip + "      - " + str(oid) + "\n"

with open('generator.yml', 'r') as gen:
    text = gen.readlines()
    
text[3] = snip

with open('generator.yml', 'w') as genOut:
    genOut.writelines(text)
    
replacements = {'RETRY': str(data['snmpMetrics']['retries']),
                'TIMEOUT': str(data['snmpMetrics']['scrapeTimeout']),
                'COMMUNITYREADSTRING': str(data['snmpMetrics']['communityString'])}

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
subprocess.run("export PATH=$PATH:/usr/local/go/bin", shell=True)
os.environ["PATH"] += os.pathsep + os.pathsep.join(["/usr/local/go/bin"])
dir = str(os.getcwd())
os.putenv("GOPATH", dir)
genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
genCmd = "yes | sudo cp -rfa generator.yml " + genLoc
subprocess.run(genCmd, shell=True)
# subprocess.run("go build", shell=True, cwd=genLoc)
# subprocess.run("make mibs", shell=True, cwd=genLoc)
print("Generating dynamic SNMP config file...")
subprocess.run("./generator generate", shell=True, cwd=genLoc)
print("Success! Configured custom SNMP Exporter container")
