import json
import os
import yaml
import sys
import re 
import site_functions

# read yml file
data,file_name = site_functions.read_yml_file("config_site",sys.argv)

switchNum = data['switchNum']
hostip = data['hostIP']
pushgatewayPort =str(data['pushgatewayPort'])
pushgateway_server = f"{data['grafanaHostIP']}:{pushgatewayPort}" 
host1IP = data['hostA']['IP']
host2IP = data['hostB']['IP']
if len(sys.argv>1):
    top_level_config_file = str(sys.argv[1])
else:
    top_level_config_file = "config.yml"
    
################################### WRITE DYNAMIC_START ###############################
# read in yaml file
with open('dynamic_start.sh', 'r') as file:
    write_data = file.readlines()
    
new_data = []
for each_line in write_data:
    each_line = re.sub("pushgateway_server=.*", f"pushgateway_server={pushgateway_server}", each_line)
    each_line = re.sub("MYIP=.*", f"MYIP={hostip}", each_line)
    each_line = re.sub("top_level_config_file=.*", f"top_level_config_file={top_level_config_file}", each_line)
    
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