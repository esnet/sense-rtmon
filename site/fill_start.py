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
top_level_config_file = data['configFile']

################################### WRITE DYNAMIC_START ###############################
# read in yaml file
with open('dynamic_start.sh', 'r') as file:
    write_data = file.readlines()
    
new_data = []
for each_line in write_data:
    each_line = re.sub("pushgateway_server=.*", f"pushgateway={pushgateway_server}", each_line)
    each_line = re.sub("MYIP=.*", f"MYIP={hostip}", each_line)
    each_line = re.sub("top_level_config_file=.*", f"top_level_config_file={top_level_config_file}", each_line)
    
    if switchNum == 1:
        switch_target1 = data['switchData']['target']
        each_line = re.sub("switch_target1=.*", f"switch_target1={switch_target1}", each_line)
    elif switchNum == 2:
        switch_target1 = data['switchDataA']['target']
        switch_target2 = data['switchDataB']['target']
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

#################################### COMPOSE FILES #################################

# change volume/config file in ARP docker file    
with open("./compose-files/arp-docker-compose.yml", 'r') as gen:
    text = gen.readlines()

new_text = []
for each_line in text:
    each_line = re.sub("      - ../../config/.*:/etc/arp_exporter/arp.yml", f"      - ../../config/{file_name}:/etc/arp_exporter/arp.yml", each_line)
    new_text.append(each_line)
    
with open('./compose-files/arp-docker-compose.yml', 'w') as genOut:
    genOut.writelines(new_text)
    
    
# change volume/config file in TCP docker file    
with open("./compose-files/tcp-docker-compose.yml", 'r') as gen:
        text = gen.readlines()

new_text = []
for each_line in text:
    each_line = re.sub("      - ../../config/.*:/etc/tcp_exporter/tcp.yml", f"      - ../../config/{file_name}:/etc/tcp_exporter/tcp.yml", each_line)
    new_text.append(each_line)
    
with open('./compose-files/tcp-docker-compose.yml', 'w') as genOut:
    genOut.writelines(new_text)