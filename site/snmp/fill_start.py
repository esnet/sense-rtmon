import sys
import re 
import yaml
import snmp_functions
# read yml file
data = snmp_functions.read_config()
                
hostip = data['hostIP']
pushgateway_server = f"{data['grafanaHostIP']}:{str(data['pushgatewayPort'])}" 
    
################################### WRITE DYNAMIC_START ###############################
# read in yaml file
with open('dynamic_start.sh', 'r') as file:
    write_data = file.readlines()
    
new_data = []
for each_line in write_data:
    each_line = re.sub("pushgateway_server=.*", f"pushgateway_server={pushgateway_server}", each_line)
    each_line = re.sub("MYIP=.*", f"MYIP={hostip}", each_line)
    
    switch_target = data['snmpMetricsA']['target']
    each_line = re.sub("switch_target=.*", f"switch_target={switch_target}", each_line)
    new_data.append(each_line)

# write out yaml file
with open('dynamic_start.sh', 'w') as file:
    file.writelines(new_data)