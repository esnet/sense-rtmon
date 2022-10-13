import yaml
import sys
import subprocess
import os
sys.path.append("..") # Adds higher directory to python modules path.
import site_functions

print("Parsing config file...")
data,file_name = site_functions.read_yml_file("config_site",sys.argv,1,2)

print("Collecting SNMP generator template...")
print("Reading SNMP OIDs/Interfaces/Scrape Duration/Scrape Time from config file...")

# SNMP scraps 1 switche
if(data['switchNum']) == 1:
    with open('./templates/generatorTemplate.yml') as inGen, open('generator.yml', 'w') as outGen:
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
# SNMP scraps 2 switches
elif(data['switchNum']) == 2:
    with open('./templates/generatorTemplate2.yml') as inGen, open('generator.yml', 'w') as outGen:
        for line in inGen:
            outGen.write(line)
    oidsA = set(data['snmpMetricsA']['oids'])
    oidsB = set(data['snmpMetricsB']['oids'])
    # read all oids in first then add to generator file
    snipA = ""
    snipB = ""
    
    for oid in oidsA:
        snipA = snipA + "      - " + str(oid) + "\n"
    for oid in oidsB:
        snipB = snipB + "      - " + str(oid) + "\n"

    with open('generator.yml', 'r') as gen:
        text = gen.readlines()
    text[3] = snipA
    text[21] = snipB
    with open('generator.yml', 'w') as genOut:
        genOut.writelines(text)
        
    replacements = {'RETRY': str(data['snmpMetricsA']['retries']),
                    'TIMEOUT': str(data['snmpMetricsA']['scrapeTimeout']),
                    'COMMUNITYREADSTRING': str(data['snmpMetricsA']['communityString']),
                    'RE2': str(data['snmpMetricsB']['retries']),
                    'TI2': str(data['snmpMetricsB']['scrapeTimeout']),
                    'CS2': str(data['snmpMetricsB']['communityString'])}
    
else:
    print("invilad switch number")
    exit
    
    
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

print("Generating dynamic SNMP config file...")

subprocess.run("./generator generate", shell=True, cwd=genLoc)
subprocess.run("yes | cp -rfa snmp.yml ../../../../../", shell=True, cwd=genLoc)
print("Success! Configured custom SNMP Exporter container")