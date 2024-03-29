import json
import os
import sys
import re 
from datetime import datetime
import cloud_functions

# get time for API keys
now = datetime.now()
current_time = now.strftime("%m/%d_%H:%M")    

# read yml file
data,file_name = cloud_functions.read_yml_file("config_flow",sys.argv,1,1)

print("!!   AUTO CURL MAY FAIL")
print("!!    Visit Google Doc for Grafana API and add Prometheus as a Data Source Key instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub")

# curl the API key to here
# curlCMD = "curl -X POST -H \"Content-Type: application/json\" -d '{\"name\":\"" +str(current_time) + "\", \"role\": \"Admin\"}' http://admin:admin@" + str(data['hostIP']) + ":3000/api/auth/keys"

# curl the API key to here
curlCMD = "curl -X POST -H \"Content-Type: application/json\" -d '{\"name\":\"" +str(current_time) + "\", \"role\": \"Admin\"}' http://admin:admin@" + str(data['grafana_host']).split("//")[1] + "/api/auth/keys"

token = os.popen(curlCMD).read()
result = re.search('"key":"(.*)"}', str(token)) # extract the API key from result
api_key = str(result.group(1))

# write the API key into config file that's used
os.chdir("..")
with open(f"config_flow/{str(sys.argv[1])}", 'r') as file:
    write_data = file.readlines()
file_data = []
for each_line in write_data:
    each_line = re.sub("grafana_api_token:.*", f"grafana_api_token: \"Bearer {api_key}\"", each_line)
    file_data.append(each_line)
with open(f"config_flow/{str(sys.argv[1])}", 'w') as file:
    file.writelines(file_data)

print(f"\nAPI Key: Bearer {api_key}")
print("!!   API CURL COMPLETE")

# curlCMD = curl -X POST -H \"Content-Type: application/json\" -d '{\"name\":\"1\", \"role\": \"Admin\"}' http://admin:admin@198.124.151.8:3000/api/auth/keys