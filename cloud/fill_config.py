import json
import os
import yaml
import sys
import re 
import cloud_functions

# read yml file
data,file_name = cloud_functions.read_yml_file("config_flow",sys.argv,1,1)
                
switchNum = data['switchNum']
hostip = data['hostIP']
pushgateway_port = str(data['pushgatewayPort'])
pushgateway_server = f"{data['grafanaHostIP']}:f{pushgateway_port}" 
host1IP = data['hostA']['IP']
host2IP = data['hostB']['IP']

# switch_num = data['switch']['num']
# hostip = data['hostIP']
# pushgateway = data['pushgateway']
# hosts_ip = []
# host_num = data['host']['num']
# for i in range(host_num):
#     hosts_ip.append(data['host'][f'host{i+1}']['ip'])
# swtich_target = []
# for i in range(switch_num):
#     swtich_target.append(data['switch'][f'switch{i+1}']['target'])

# read in args.sh file
with open('./se_config/args.sh', 'r') as file:
    write_data = file.readlines()

args_data = []
for each_line in write_data:
    each_line = re.sub("pushgateway=.*", f"pushgateway={hostip}", each_line)
    each_line = re.sub("host1=.*", f"host1={host1IP}", each_line)
    each_line = re.sub("host2=.*", f"host2={host2IP}", each_line)
    each_line = re.sub("switch_num=.*", f"switch_num={str(switchNum)}", each_line)
    switch_target1 = data['switchDataA']['target']
    each_line = re.sub("switch_ip1=.*", f"switch_ip1={switch_target1}", each_line)
    if switchNum == 2:
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