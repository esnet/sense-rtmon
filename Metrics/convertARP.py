import re
import json
import sys

filename = sys.argv[1]
with open(filename) as file:
    lines = file.readlines()
    lines = [line.rstrip() for line in lines]

json_file = open('arp.json', 'w')
json_file.write("{\n")
for line in lines:
    dump = {}
    dump['hostname']  = re.findall(r'^(.*?)\s', line)[0]
    #dump['mac'] = re.findall(r'([0-9a-f]{1,2}[\.:-]){5}([0-9a-f]{1,2})', line)[0]
    dump['ip']  = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)[0]
    json.dump(dump, json_file)
    json_file.write(",\n")
json_file.write("}")
json_file.close()