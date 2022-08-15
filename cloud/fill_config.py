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

# read in args.sh file
with open('./se_config/args.sh', 'r') as file:
    write_data = file.readlines()
    
write_data[1] = f"pushgateway={pushgateway_server}\n"
write_data[2] = f"host1={host1IP}\n"

if hostip == host2IP and hostip == host1IP:
    print("host1 and host2 cannot have the same IP address in the config file. Exiting...")
    exit
else:
    write_data[3] = f"host1={host2IP}\n"
write_data[4]=f"switch_num={switchNum}\n"

if switchNum == 1:
    switch_target1 = data['switchData']['target']
    write_data[5] = f"switch_ip1={switch_target1}\n"
elif switchNum == 2:
    switch_target1 = data['switchDataA']['target']
    switch_target2 = data['switchDataB']['target']
    write_data[5] = f"switch_ip1={switch_target1}\n"
    write_data[6] = f"switch_ip2={switch_target2}\n"
    
with open('./se_config/args.sh', 'w') as file:
    file.writelines(write_data)

# read in multiDef.sh file
with open('./se_config/multiDef.sh', 'r') as file:
    write_data = file.readlines()
    
write_data[1] = f"pushgateway={pushgateway_server}\n"
write_data[2] = f"host1={host1IP}\n"

if hostip == host2IP and hostip == host1IP:
    print("host1 and host2 cannot have the same IP address in the config file. Exiting...")
    exit
else:
    write_data[3] = f"host1={host2IP}\n"
write_data[4]=f"switch_num={switchNum}\n"

if switchNum == 1:
    switch_target1 = data['switchData']['target']
    write_data[5] = f"switch_ip1={switch_target1}\n"
elif switchNum == 2:
    switch_target1 = data['switchDataA']['target']
    switch_target2 = data['switchDataB']['target']
    write_data[5] = f"switch_ip1={switch_target1}\n"
    write_data[6] = f"switch_ip2={switch_target2}\n"
    
with open('./se_config/multiDef.sh', 'w') as file:
    file.writelines(write_data)