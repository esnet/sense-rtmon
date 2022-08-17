import json
import os
import yaml
import sys
import re 
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
    each_line = re.sub("pushgateway=.*", f"pushgateway={hostip}", each_line)
    each_line = re.sub("host1=.*", f"host1={host1IP}", each_line)
    each_line = re.sub("host2=.*", f"host2={host2IP}", each_line)
    each_line = re.sub("switch_num=.*", f"switch_num={str(switchNum)}", each_line)
    if switchNum == 1:
        switch_target1 = data['switchData']['target']
        each_line = re.sub("switch_ip1=.*", f"switch_ip1={switch_target1}", each_line)
    elif switchNum == 2:
        switch_target1 = data['switchDataA']['target']
        switch_target2 = data['switchDataB']['target']
        each_line = re.sub("switch_ip1=.*", f"switch_ip1={switch_target1}", each_line)
        each_line = re.sub("switch_ip2=.*", f"switch_ip2={switch_target2}", each_line)
    args_data.append(each_line)
    
with open('./se_config/args.sh', 'w') as file:
    file.writelines(args_data)

# read in multiDef.sh file
if switchNum >= 2:
    with open('./se_config/multiDef.sh', 'r') as file:
        write_data = file.readlines()

    mult_data = []
    for each_line in write_data:
        each_line = re.sub("pushgateway=.*", f"pushgateway={hostip}", each_line) # ip address instead
        each_line = re.sub("host1=.*", f"host1={host1IP}", each_line)
        each_line = re.sub("host2=.*", f"host2={host2IP}", each_line)
        each_line = re.sub("switch_num=.*", f"switch_num={str(switchNum)}", each_line)
        switch_target1 = data['switchDataA']['target']
        switch_target2 = data['switchDataB']['target']
        each_line = re.sub("switch_ip1=.*", f"switch_ip1={switch_target1}", each_line)
        each_line = re.sub("switch_ip2=.*", f"switch_ip2={switch_target2}", each_line)
        mult_data.append(each_line)
        
    with open('./se_config/multiDef.sh', 'w') as file:
        file.writelines(mult_data)


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