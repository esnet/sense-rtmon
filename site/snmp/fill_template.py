import sys
import re 
import yaml
import os
# data = snmp_functions.read_config()
import json

with open("generator_template.yml") as inGen, open("generator.yml", 'w') as outGen:
    for line in inGen:
        outGen.write(line)
# oids = set(str(os.environ["OIDS_LIST"]))
oids = json.loads(os.environ['OIDS_LIST'])

# read all oids in first then add to generator file
snip = ""
for oid in oids:
    snip = snip + "      - " + str(oid) + "\n"
with open("generator.yml", 'r') as gen:
    text = gen.readlines()
text[3] = snip
with open("generator.yml", 'w') as genOut:
    genOut.writelines(text)
    
replacements = {'RETRY': str(os.environ["RETRY"]),
                'TIMEOUT': str(os.environ["TIMEOUT"]),
                'COMMUNITYREADSTRING': str(os.environ["COMMUNITY_STRING"])} 

# Read in the file
with open("generator.yml", 'r') as file:
    filedata = file.read()
# Replace the target string
for k,v in replacements.items():
    filedata = filedata.replace(k, v)
# Write the file out again
with open("generator.yml", 'w') as file:
    file.write(filedata)
