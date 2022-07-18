# parsing the main config.yml and dynamically create layer 2 arguments
import os
import yaml
        
config_data ={}
owd = os.getcwd()
os.chdir("..")
infpth = str(os.path.abspath(os.curdir)) + "/config.yml"
os.chdir(owd)

print("Loading Configuration File")
with open(infpth, 'r') as stream:
    try:
        config_data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("Config file load error!")

print("Parsing Config File")        
receiver_ip_address = "http://" + str(config_data['grafanaHostIP'])

pushgateway_ip = str(config_data['hostIP'])
switch_num = str(config_data['switchNum'])
host1 = str(config_data['hostA']['IP'])
host2 = str(config_data['hostB']['IP'])
vlan_num = str(config_data['vlan_to_switch'])
with open('se_config/config.yaml', 'r') as file:
    data = file.readlines()

if switch_num == "1":
    print("1 switch detected")
    switch_ip1 = str(config_data['switchData']['SNMPHostIP'])
    data[-1] = f"    script: ./examples/args.sh {pushgateway_ip} {host1} {host2} {switch_num} {vlan_num} {switch_ip1} 0" # means no second switch 
elif switch_num == "2":
    print("2 switch detected")
    switch_ip1 = str(config_data['switchDataA']['SNMPHostIP'])
    switch_ip2 = str(config_data['switchDataB']['SNMPHostIP'])
    data[-1] = f"    script: ./examples/args.sh {pushgateway_ip} {host1} {host2} {switch_num} {vlan_num} {switch_ip1} {switch_ip2}" 
else:
    print("Wrong Number of Switches Detected")
    print("No modification made")
    quit()
    
with open('se_config/config.yaml', 'w') as file:
    file.writelines(data)

print("Parsing Completed")