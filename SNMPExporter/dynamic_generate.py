import yaml
import sys
import subprocess
import os

print("Starting script...")

# read from main config.yml
data = {}
owd = os.getcwd()
os.chdir("..")
infpth = str(os.path.abspath(os.curdir)) + "/config.yml"
os.chdir(owd)
with open(infpth, 'r') as stream:
    data = yaml.safe_load(stream)

with open('generatorTemplate.yml') as inGen, open('generator.yml', 'w') as outGen:
        for line in inGen:
            outGen.write(line)

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
with open('generator.yml', 'w') as file:
    file.write(filedata)
    
dir = str(os.getcwd())
genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
genCmd = "yes | cp -rfa generator.yml " + genLoc
subprocess.run(genCmd, shell=True)

subprocess.run("./generator generate", shell=True, cwd=genLoc)
subprocess.run("yes | cp -rfa snmp.yml ../../../../../", shell=True, cwd=genLoc)
print("Success! Configured custom SNMP Exporter container")