import json
import os

# Open the input file
input_file = "received_config.json"
prev_file = "prev_config.json"
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
                
    # Write the data to the prev file for record
    json.dump(prev_file)

# Process the data, extract information
example_data = {
    "exporter": "snmp",
    "pushgateway": "dev2.virnao.com:9091",
    "target": "132.249.2.46",
    "name":"Caltech_Switch",
    # "oids": ["ifMIB", "ifMtu", "ifName", "ifPhysAddress", "ifIndex", "ifType"],
    "oids": ["ifName"],
    "community_string": "",
    "status": 1
}

# Open the output file
with open('push_snmp_exporter_metrics', 'w') as f:
    # default values
    TARGET = os.getenv('TARGET')
    SNMP_PORT = os.getenv('SNMP_PORT')
    NAME = os.getenv('NAME')
    PUSHGATEWAY = os.getenv('PUSHGATEWAY')
    
    new_config = f'''
    #! /bin/bash
    if curl localhost:9116/metrics | grep ".*"; then
        curl -o /home/snmp_temp.txt localhost:{SNMP_PORT}/snmp?target=${TARGET}&module=if_mib
    else
        > /home/snmp_temp.txt	
    fi
    cat /home/snmp_temp.txt | curl --data-binary @- ${PUSHGATEWAY}/metrics/job/snmp-exporter/target_switch/${TARGET}/instance/${NAME}
    '''
    
    # Write the processed data to the output file
    if "pushgateway" in data:
        PUSHGATEWAY = data["pushgateway"]
    if "name" in data:
        NAME = data["name"]
    if "target" in data:
        TARGET = data["target"]
    if SNMP_PORT in data:
        SNMP_PORT = data["snmp_port"]

    if "status" in data:
        if data["status"] == 0:
            new_config =f'''
            #! /bin/bash
            echo "Exporter Turned Off by Cloud Stack"
            '''
    
    f.write(new_config)
    
