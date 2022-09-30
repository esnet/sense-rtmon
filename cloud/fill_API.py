import json
import os
import yaml
import sys
import re 
from datetime import datetime
# get time for API keys
now = datetime.now()
current_time = now.strftime("%m/%d_%H:%M")
    
# get this host's IP address
owd = os.getcwd()
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config_cloud"
infpth = config_path + "/config.yml"
os.chdir(owd)
data = {}
file_name = "config.yml"

print("!!   AUTO CURL MAY FAIL")
print("!!    Visit Google Doc for Grafana API and add Prometheus as a Data Source Key instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub")

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
        
    # curl the API key to here
    curlCMD= "curl 'http://admin:admin@" + str(data['hostIP']) + ":3000/api/auth/keys' -XPOST -H 'Content-Type: application/json' -d '{\"role\":\"Admin\",\"name\":\"" + current_time + "\"}'"
    token = os.popen(curlCMD).read()
    result = re.search('"key":"(.*)"}', str(token)) # extract the API key from result
    # write the API key into config file that's used
    with open(file_path, 'r') as file:
        write_data = file.readlines()
    file_data = []
    for each_line in write_data:
        each_line = re.sub("grafanaAPIToken:.*", f"grafanaAPIToken: \"Bearer {str(result.group(1))}\"", each_line)
        file_data.append(each_line)
    with open(file_path, 'w') as file:
        file.writelines(file_data)
        
else: # default config file
    with open(infpth, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {infpth} could not be found in the config directory\n")
    
    # curl the API key to here
    curlCMD= "curl 'http://admin:admin@" + str(data['hostIP']) + ":3000/api/auth/keys' -XPOST -H 'Content-Type: application/json' -d '{\"role\":\"Admin\",\"name\":\"" + current_time + "\"}'"
    token = os.popen(curlCMD).read()
    result = re.search('"key":"(.*)"}', str(token)) # extract the API key from result
    # write the API key into config file that's used
    with open(infpth, 'r') as file:
        write_data = file.readlines()
    file_data = []
    for each_line in write_data:
        each_line = re.sub("grafanaAPIToken:.*", f"grafanaAPIToken: \"Bearer {str(result.group(1))}\"", each_line)
        file_data.append(each_line)
    with open(infpth, 'w') as file:
        file.writelines(file_data)
        
    print("!!   API CURL SUCCESS!")