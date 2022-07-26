import json
import os
import yaml
import sys

# get this host's IP address
owd = os.getcwd()
os.chdir("..")
infpth = str(os.path.abspath(os.curdir)) + "/config.yml"
config_path = str(os.path.abspath(os.curdir))
os.chdir(owd)
data = {}

# argument given
if len(sys.argv) > 1:
    file_name = str(sys.argv[1])
    file_path = config_path + "/" + file_name
    print(f"\n Config file {file_path}\n")
    with open(file_path, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {file_path} could not be found in the DynamicDashboard directory\n")
else: # default config file
    with open(infpth, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {infpth} could not be found in the DynamicDashboard directory\n")
            
hostip = data['hostIP']
pushgateway_server = f"{data['grafanaHostIP']}:9091" 
host2IP = data['hostB']['IP']
top_level_config_file = data['configFile']

with open('start.sh', 'r') as file:
    write_data = file.readlines()
    
write_data[8] = f"MYIP={hostip}\n"
write_data[9] = f"pushgateway_server={pushgateway_server}\n"
write_data[10] = f"host2IP={host2IP}\n"
write_data[11] = f"top_level_config_file={top_level_config_file}\n"

# data[7] = f"switch_ip2=0\n" # means no second switch
with open('start.sh', 'w') as file:
    file.writelines(write_data)