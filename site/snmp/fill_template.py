import sys
import re 
import yaml
import snmp_functions
import os
data = snmp_functions.read_config()

with open("generator_template.yml") as inGen, open("generator.yml", 'w') as outGen:
    for line in inGen:
        outGen.write(line)
oids = set(data[f'snmpMetricsA']['oids'])
# read all oids in first then add to generator file
snip = ""
for oid in oids:
    snip = snip + "      - " + str(oid) + "\n"
with open("generator.yml", 'r') as gen:
    text = gen.readlines()
text[3] = snip
with open("generator.yml", 'w') as genOut:
    genOut.writelines(text)
    
replacements = {'RETRY': str(data[f'snmpMetricsA']['retries']),
                'TIMEOUT': str(data[f'snmpMetricsA']['scrapeTimeout']),
                'COMMUNITYREADSTRING': str(os.environ["COMMUNITY_STRING"])} #str(data[f'snmpMetricsA']['communityString'])

# Read in the file
with open("generator.yml", 'r') as file:
    filedata = file.read()
# Replace the target string
for k,v in replacements.items():
    filedata = filedata.replace(k, v)
# Write the file out again
with open("generator.yml", 'w') as file:
    file.write(filedata)
