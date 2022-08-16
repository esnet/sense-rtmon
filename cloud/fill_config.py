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

args_data = []
for each_line in write_data:
    each_line = each_line.replace("pushgateway=$1", pushgateway_server, 1)
    each_line = each_line.replace("host1=$2", host1IP, 1)
    each_line = each_line.replace("host2=$3", host2IP, 1)
    each_line = each_line.replace("switch_num=$4", str(switchNum), 1)
    if switchNum == 1:
        switch_target1 = data['switchData']['target']
        each_line = each_line.replace("switch_ip1=$5", switch_target1, 1)
    elif switchNum == 2:
        switch_target1 = data['switchDataA']['target']
        switch_target2 = data['switchDataB']['target']
        each_line = each_line.replace("switch_ip1=$5", switch_target1, 1)
        each_line = each_line.replace("switch_ip2=$6", switch_target2, 1)
    args_data.append(each_line)
    
with open('./se_config/args.sh', 'w') as file:
    file.writelines(args_data)

# read in multiDef.sh file
with open('./se_config/multiDef.sh', 'r') as file:
    write_data = file.readlines()

mult_data = []
for each_line in write_data:
    each_line = each_line.replace("pushgateway=$1", pushgateway_server, 1)
    each_line = each_line.replace("host1=$2", host1IP, 1)
    each_line = each_line.replace("host2=$3", host2IP, 1)
    each_line = each_line.replace("switch_num=$4", str(switchNum), 1)
    if switchNum == 1:
        switch_target1 = data['switchData']['target']
        each_line = each_line.replace("switch_ip1=$5", switch_target1, 1)
    elif switchNum == 2:
        switch_target1 = data['switchDataA']['target']
        switch_target2 = data['switchDataB']['target']
        each_line = each_line.replace("switch_ip1=$5", switch_target1, 1)
        each_line = each_line.replace("switch_ip2=$6", switch_target2, 1)
    mult_data.append(each_line)
    
with open('./se_config/multiDef.sh', 'w') as file:
    file.writelines(mult_data)


# read in promethues.yml file 
with open('./dashboard/prometheus.yml', 'r') as file:
    write_data = file.readlines()

new_data = []
hostip = data['hostIP']
for each_line in write_data:
    each_line = each_line.replace("your_ip", hostip, 1)
    new_data.append(each_line)
    
with open('./dashboard/prometheus.yml', 'w') as file:
    file.writelines(new_data)