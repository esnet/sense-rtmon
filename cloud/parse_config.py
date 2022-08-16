# parsing the main config.yml and dynamically create layer 2 arguments
import os
import yaml
import sys
        
config_data ={}
owd = os.getcwd()
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config"
infpth = config_path + "/config.yml"
os.chdir(owd)
            
print("Loading Configuration File")
# argument given
if len(sys.argv) > 1:
    file_name = str(sys.argv[1])
    file_path = config_path + "/" + file_name
    print(f"\n Config file {file_path}\n")
    with open(file_path, 'r') as stream:
        try:
            config_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {file_path} could not be found in the config directory\n")
else: # default config file
    with open(infpth, 'r') as stream:
        try:
            config_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {infpth} could not be found in the config directory\n")


print("Parsing Config File")        
pushgateway_ip = str(config_data['hostIP'])
switch_num = str(config_data['switchNum'])
host1 = str(config_data['hostA']['IP'])
host2 = str(config_data['hostB']['IP'])
# flow_vlan = str(config_data['vlan_to_switch'])

if switch_num == "1":
    print("1 switch detected")
    with open('se_config/args.sh', 'r') as file:
        data = file.readlines()
    data[1] = f"pushgateway={pushgateway_ip}\n"
    data[2] = f"host1={host1}\n"
    data[3] = f"host2={host2}\n"
    data[4] = f"switch_num={switch_num}\n"
    data[5] = f"flow_vlan={flow_vlan}\n"
    switch_ip1 = str(config_data['switchData']['target'])
    data[6] = f"switch_ip1={switch_ip1}\n"
    # data[7] = f"switch_ip2=0\n" # means no second switch
    with open('se_config/args.sh', 'w') as file:
        file.writelines(data)
     
elif switch_num == "2":
    print("2 switch detected")
    with open('se_config/multiDef.sh', 'r') as file:
        data = file.readlines()
    data[1] = f"pushgateway={pushgateway_ip}\n"
    data[2] = f"host1={host1}\n"
    data[3] = f"host2={host2}\n"
    data[4] = f"switch_num={switch_num}\n"
    data[5] = f"flow_vlan={flow_vlan}\n"
    switch_ip1 = str(config_data['switchDataA']['target'])
    switch_ip2 = str(config_data['switchDataB']['target'])
    data[6] = f"switch_ip1={switch_ip1}\n"
    data[7] = f"switch_ip2={switch_ip2}\n"
    with open('se_config/multiDef.sh', 'w') as file:
        file.writelines(data)
else:
    print("Wrong Number of Switches Detected")
    print("No modification made")
    quit()

print("Parsing Completed")