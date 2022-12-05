import re 
import yaml

# read yml file
data = {} 
with open("config.yml", 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(f"\n Config file config.yml could not be found in the config directory\n")
                
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
    new_data.append(each_line)

# write out yaml file
with open('dynamic_start.sh', 'w') as file:
    file.writelines(new_data)