import yaml
import sys
import re 

# read yml file
data = {} 
with open("config.yml", 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(f"\n Config file config.yml could not be found in the config directory\n")
        
hostip = data['hostIP']
host1IP = data['hostA']['IP']
host2IP = data['hostB']['IP']    

# read in yaml file
with open('dynamic_start.sh', 'r') as file:
    write_data = file.readlines()
    
new_data = []
for each_line in write_data:
    if hostip == host1IP: # if this machine is host1 then the other is host2
        each_line = re.sub("host2IP=.*", f"host2IP={host2IP}", each_line)
    elif hostip == host2IP: # if this machine is host2 then the other is host1
        each_line = re.sub("host2IP=.*", f"host2IP={host1IP}", each_line)

    new_data.append(each_line)

# write out yaml file
with open('dynamic_start.sh', 'w') as file:
    file.writelines(new_data)