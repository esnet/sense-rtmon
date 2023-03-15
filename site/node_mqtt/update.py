import json
import os
import requests
import re

# Open the input file
input_file = "/home/received_config.json"
prev_file = "/home/prev_config.json"
if os.path.exists(input_file) != True:
    print("File does not exist")
    exit(0)
    
with open(input_file, 'r') as f:
    # Load the data from the input file
    data = json.load(f)

    # if not change in file exit
    # if os.path.exists(prev_file) == True:
    #     with open(prev_file, 'r') as f:
    #         prev_data = json.load(f)
    #         if data == prev_data:
    #             print("No change in config")
    #             exit(0)
                
    with open(prev_file, 'w') as outfile:
    # Write the data to the prev file for record
        json.dump(data,outfile)

# Process the data, extract information
example_data = {
    "exporter": "node",
    "pushgateway": "dev2.virnao.com:9091",
    "name":"ucsd",
    "status": 1,
    "device": "sdn-dtn-2-10.ultralight.org",
    "delete": "yes"
}

def find_string_between_strings(text, str1, str2):
    pattern = f"{re.escape(str1)}(.*?){re.escape(str2)}"
    result = re.findall(pattern, text, re.DOTALL)
    return result

# Open the output file
with open('/home/push_node_exporter_metrics.sh', 'r+') as f:
    # default values
    file_contents = f.read()
    NODE_PORT = find_string_between_strings(file_contents, "localhost:", "/metrics |")
    PUSHGATEWAY = find_string_between_strings(file_contents, "@- :", "/metrics/job")
    NAME = find_string_between_strings(file_contents, "instance/", "")
    
    # Write the processed data to the output file
    if "pushgateway" in data:
        PUSHGATEWAY = data["pushgateway"]
    if "name" in data:
        NAME = data["name"]

    new_config = f'''#! /bin/bash
curl -s localhost:{NODE_PORT}/metrics | curl --data-binary @- {PUSHGATEWAY}/metrics/job/node-exporter/instance/{NAME}
    '''
    
    if "status" in data:
        if data["status"] == 0:
            new_config =f'''
            #! /bin/bash
            echo "Exporter Turned Off by Cloud Stack"
            '''
    
    if "delete" in data:
        if 'y' in data["delete"].lower():
            delete_url = f'{PUSHGATEWAY}/metrics/job/node-exporter/instance/{NAME}'
            print("Deleting the following group: ")
            print(delete_url)
            print("")
            # delete the url (same as Delete Group button)
            requests.delete(delete_url)

    
    
    f.write(new_config)