import sys
import re 
sys.path.append("..") # Adds higher directory to python modules path.
import site_functions

# read yml file
data,file_name = site_functions.read_yml_file("",sys.argv)

hostip = data['hostIP']
pushgateway_server = f"{data['grafanaHostIP']}:{str(data['pushgatewayPort'])}" 

if len(sys.argv) > 1:
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
    new_data.append(each_line)

# write out yaml file
with open('dynamic_start.sh', 'w') as file:
    file.writelines(new_data)