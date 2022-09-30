import json
import os
import yaml
import sys
import re 

# get this host's IP address
owd = os.getcwd()
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config_cloud"
infpth = config_path + "/config.yml"
os.chdir(owd)
data = {}
file_name = "config.yml"

# argument given
if len(sys.argv) > 1:
    file_name = str(sys.argv[1])
    file_path = config_path + "/" + file_name
    print(f"\n Config file {file_path}\n")
    with open(file_path, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {file_path} could not be found in the config directory\n")
        
else: # default config file
    with open(infpth, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {infpth} could not be found in the config directory\n")
                
# read in promethues.yml file 
with open('prometheus.yml', 'r') as file:
    write_data = file.readlines()

new_data = []
hostip = data['hostIP']
for each_line in write_data:
    each_line = re.sub("'.*:9090", f"'{hostip}:9090", each_line) # different format for 9090
    each_line = re.sub("- .*:9091", f"- {hostip}:9091", each_line)
    each_line = re.sub("- .*:9469", f"- {hostip}:9469", each_line)
    new_data.append(each_line)
    
with open('prometheus.yml', 'w') as file:
    file.writelines(new_data)
