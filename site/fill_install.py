import json
import os
import yaml
import sys

# get this host's IP address
owd = os.getcwd()
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config"
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

switchNum = data['switchNum']
hostip = data['hostIP']
pushgateway_server = f"{data['grafanaHostIP']}:9091" 
host1IP = data['hostA']['IP']
host2IP = data['hostB']['IP']

# read in yaml file
with open('dynamic_install.sh', 'r') as file:
    write_data = file.readlines()
    
write_data[6] = f"MYIP={hostip}\n"
write_data[7] = f"pushgateway_server={pushgateway_server}\n"

if hostip == host2IP and hostip == host1IP:
    print("host1 and host2 cannot have the same IP address in the config file. Exiting...")
    exit
elif hostip == host1IP: # if this machine is host1 then the other is host2
    write_data[8] = f"host2IP={host2IP}\n"
elif hostip == host2IP: # if this machine is host2 then the other is host1
    write_data[8] = f"host2IP={host1IP}\n"
s
# write out yaml file
with open('dynamic_install.sh', 'w') as file:
    file.writelines(write_data)
