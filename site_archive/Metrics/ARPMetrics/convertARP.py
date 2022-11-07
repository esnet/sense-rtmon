import re
import json
import sys

filename = sys.argv[1]
with open(filename) as file:
    lines = file.readlines()
    lines = [line.rstrip() for line in lines]

outFile = sys.argv[2]
json_file = open(outFile, 'w')
json_file.write("[\n")
for line in lines:
    try:
        dump = {}
        dump['hostname']  = re.findall(r'^(.*?)\s', line)[0]
        dump['mac'] = re.findall(r'(?:[0-9a-fA-F]:?){12}', line)[0]
        dump['ip']  = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)[0]
        json.dump(dump, json_file)
        json_file.write(",\n")
    except IndexError:
        continue
json_file.write("]")
json_file.close()
