import json
import os
import yaml
import sys
import re 
import site_functions

# read yml file
data = {} 
with open("config.yml", 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(f"\n Config file config.yml could not be found in the config directory\n")

switchNum = data['switchNum']
hostip = data['hostIP']
host1IP = data['hostA']['IP']
host2IP = data['hostB']['IP']
    
################################### WRITE DYNAMIC_START ###############################
# read in yaml file
with open('dynamic_start.sh', 'r') as file:
    write_data = file.readlines()
    
new_data = []
for each_line in write_data:
    each_line = re.sub("MYIP=.*", f"MYIP={hostip}", each_line)
    each_line = re.sub("switchNum=.*", f"switchNum={switchNum}", each_line)

    if switchNum == 1:
        switch_target1 = data['snmpMetricsA']['target']
        each_line = re.sub("switch_target1=.*", f"switch_target1={switch_target1}", each_line)
        each_line = re.sub("switch_target2=.*", f"switch_target2=", each_line)

    elif switchNum == 2:
        switch_target1 = data['snmpMetricsA']['target']
        switch_target2 = data['snmpMetricsB']['target']
        each_line = re.sub("switch_target1=.*", f"switch_target1={switch_target1}", each_line)
        each_line = re.sub("switch_target2=.*", f"switch_target2={switch_target2}", each_line)
    
    if hostip == host1IP: # if this machine is host1 then the other is host2
        each_line = re.sub("host2IP=.*", f"host2IP={host2IP}", each_line)
    elif hostip == host2IP: # if this machine is host2 then the other is host1
        each_line = re.sub("host2IP=.*", f"host2IP={host1IP}", each_line)

    new_data.append(each_line)

# write out yaml file
with open('dynamic_start.sh', 'w') as file:
    file.writelines(new_data)