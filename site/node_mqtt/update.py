import json
import os

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
    if os.path.exists(prev_file) == True:
        with open(prev_file, 'r') as f:
            prev_data = json.load(f)
            if data == prev_data:
                print("No change in config")
                exit(0)
                
    with open(prev_file, 'w') as outfile:
    # Write the data to the prev file for record
        json.dump(data,outfile)

# Process the data, extract information
example_data = {
    "exporter": "node",
    "pushgateway": "dev2.virnao.com:9091",
    "name":"my_computer",
    "status": 1
}

# Open the output file
with open('push_node_exporter_metrics.sh', 'w') as f:
    # default values
    NODE_PORT = str(os.getenv('NODE_PORT'))
    NAME = str(os.getenv('NAME'))
    PUSHGATEWAY = str(os.getenv('PUSHGATEWAY'))
    
    # Write the processed data to the output file
    if "pushgateway" in data:
        PUSHGATEWAY = data["pushgateway"]
    if "name" in data:
        NAME = data["name"]

    new_config = f'''
    #! /bin/bash
    curl -s localhost:{NODE_PORT}/metrics | curl --data-binary @- {PUSHGATEWAY}/metrics/job/node-exporter/instance/{NAME}
    '''
    
    if "status" in data:
        if data["status"] == 0:
            new_config =f'''
            #! /bin/bash
            echo "Exporter Turned Off by Cloud Stack"
            '''
    
    f.write(new_config)
    
