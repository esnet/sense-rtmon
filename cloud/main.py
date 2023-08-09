import subprocess
import logging
import time
import json
import sys
import requests
import re 
import os
from datetime import datetime
from time import gmtime, strftime
#from converter import orchestratorConvert
from sense.client.workflow_combined_api import WorkflowCombinedApi
from sense.client.discover_api import DiscoverApi
# from generate_s import *
from dynamic import *
from dispatch import *
from converter import converter
logging.basicConfig(filename='output.log', level=logging.DEBUG)


def fetch_data():
    response = ""
    
    try:
        response = DiscoverApi().discover_service_instances_get()
        print("Response Sucessful")
        logging.info("Response Sucessful")
    except:
        logging.critical("API Call Failed! Network Error")
        print("API Call Failed! Network Error")
        
    
    if response == "":
        logging.error("No Data")
       
    
    data = json.loads(response)
    with open("response.json", 'w') as f:
        json.dump(data, f, indent=3)
    
    return data

def filter_data(data):
    for instance in data['instances']:
        for intent in instance['intents']:
            intent['json'] = json.loads(intent['json'])
    
    filtered_data = [instance for instance in data['instances'] if instance['state'] in ["CREATE - READY", "REINSTATE - READY"]]

    with open("filtered.json", 'w') as f:
        json.dump(filtered_data, f, indent=3)

    if not filtered_data:
        logging.warning("No instances are CREATE/REINSTATE-ready.")
    else:
        logging.info("Filter Successful")
    
    return filtered_data

def create_manifest(instance):
    template = {
        "Ports": [
            {
                "Port": "?terminal?",
                "Name": "?port_name?",
                "Vlan": "?vlan?",
                "Node": "?node_name?",
                "Peer": "?peer?",
                "Site": "?site?",
                "Host": [
                    {
                        "Name": "?host_name?",
                        "Interface": "?host_port_name?",
                        "IPv4": "?ipv4?",
                        "sparql": "SELECT DISTINCT ?host_port ?ipv4 WHERE { ?vlan_port nml:isAlias ?host_vlan_port. ?host_port nml:hasBidirectionalPort ?host_vlan_port. ?host_vlan_port mrs:hasNetworkAddress  ?ipv4na. ?ipv4na mrs:type \"ipv4-address\". ?ipv4na mrs:value ?ipv4. }",
                        "sparql-ext": "SELECT DISTINCT ?host_name ?host_port_name  WHERE {?host a nml:Node. ?host nml:hasBidirectionalPort ?host_port. OPTIONAL {?host nml:name ?host_name.} OPTIONAL {?host_port mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?host_port_name.} }",
                        "required": "false"
                    }
                ],
                "sparql": "SELECT DISTINCT  ?vlan_port  ?vlan  WHERE { ?subnet a mrs:SwitchingSubnet. ?subnet nml:hasBidirectionalPort ?vlan_port. ?vlan_port nml:hasLabel ?vlan_l. ?vlan_l nml:value ?vlan. }",
                "sparql-ext": "SELECT DISTINCT ?terminal ?port_name ?node_name ?peer ?site WHERE { {?node a nml:Node. ?node nml:name ?node_name. ?node nml:hasBidirectionalPort ?terminal.  ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL {?terminal mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?port_name.} OPTIONAL {?terminal nml:isAlias ?peer.} OPTIONAL {?site nml:hasNode ?node.} OPTIONAL {?site nml:hasTopology ?sub_site. ?sub_site nml:hasNode ?node.} } UNION { ?site a nml:Topology. ?site nml:name ?node_name. ?site nml:hasBidirectionalPort ?terminal. ?terminal nml:hasBidirectionalPort ?vlan_port. OPTIONAL {?terminal mrs:hasNetworkAddress ?na_pn. ?na_pn mrs:type \"sense-rtmon:name\". ?na_pn mrs:value ?port_name.} OPTIONAL {?terminal nml:isAlias ?peer.}}}",
                "required": "true"
            }
        ]
    }
    workflowApi = WorkflowCombinedApi()
    workflowApi.si_uuid = instance['referenceUUID']
    response = workflowApi.manifest_create(json.dumps(template))
    json_response = json.loads(response)
    manifest = json.loads(json_response['jsonTemplate'])
    logging.info("Manifest Created")
    

    return manifest

def fill_API(data):
    try:
        with open('api_key.txt', 'r') as file:
            api_key = file.read().strip()
            if api_key:
                data['grafana_api_token'] = "Bearer " + api_key
    except:
        # get time for API keys
        now = datetime.now()
        current_time = now.strftime("%m/%d_%H:%M")    

        # curl the API key to here
        curlCMD = "curl -X POST -H \"Content-Type: application/json\" -d '{\"name\":\"" +str(current_time) + "\", \"role\": \"Admin\"}' http://admin:admin@" + str(data['grafana_host']).split("//")[1] + "/api/auth/keys"

        token = os.popen(curlCMD).read()
        result = re.search('"key":"(.*)"}', str(token)) # extract the API key from result
        api_key = str(result.group(1))

        # write the API key into the data dictionary
        data['grafana_api_token'] = "Bearer " + api_key

        # write the API key to a file
        with open('api_key.txt', 'w') as file:
            file.write(api_key)

        logging.info(f"\nAPI Key: Bearer {api_key}")
        logging.info("!!   API CURL COMPLETE")
    with open("data.json", 'w') as f:
        json.dump(data, f, indent=2)

    return data , api_key

# def generate_dashboard(data):
#     generate_script(data)
#     os.system('yes | cp -rfa se_config/. script_exporter/examples')
#     os.system('yes | docker rm -f $(docker ps -a --format "{{.Names}}" | grep "script_exporter")')
#     dynamic(data)

def delete_dashboard(uid, api_token, grafana_url, name):
    url = f"{grafana_url}/api/dashboards/uid/{uid}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Send the DELETE request
    response = requests.delete(url, headers=headers)

    # Check the status code of the response
    if response.status_code == 200:
        print("\033[91m" + f"Dashboard uid : {uid}, name: {name}, deleted successfully." + "\033[0m")
        time.sleep(1)
        return response.json()
    else:
        print(f"Failed to delete dashboard {uid}. Status code: {response.status_code}")
        time.sleep(1)
        return None

def main():
    live_dashboard = {}
    dashboard_recorder = {}
    while True:
        if len(live_dashboard) != 0:
            lkj = 1
            print("This are the dashboard right now")
            for id in dashboard_recorder:
                print("\033[32m" + f"{lkj}. Name: {dashboard_recorder[id]['name']}" + "\033[0m")
                lkj += 1
        response_fetched = {}
        try:
            data = fetch_data()
            
            time.sleep(1)
        except:
            logging.error("Failed to fetch data. API Error\nMaking another request in 3 mins.")
            print("Failed to fetch data. API Error\nMaking another request in 3 mins.")
            time.sleep(180)
            continue
        
        #Filter the data || only process the data that are create-ready or reinstate-ready
        try:
            data = filter_data(data)
           
            time.sleep(1)
        except:
            logging.error("Failed to filter data. \nMaking another attempt in 3 mins.")
            print("Failed to filter data. \nMaking another attempt in 3 mins.")
            time.sleep(180)
            continue
        
        if (len(live_dashboard)) == 0 and (not data):
            logging.error("Failed to filter data. \nMaking another attempt in 3 mins.")
            print("Failed to filter data. \nMaking another attempt in 3 mins.")
            time.sleep(180)
            continue
        elif not data:
            for i in list(live_dashboard):
                uid = dashboard_recorder[i]['uid']
                api = dashboard_recorder[i]['api']
                url = dashboard_recorder[i]['url']
                name = dashboard_recorder[i]['name']
                delete_dashboard(uid, api , url , name)
                dashboard_recorder.pop(i, None)
                live_dashboard.pop(i, None)
                time.sleep(1)
        
        for instance in data:
            id = instance['intents'][0]['json']['service_instance_uuid']
            name = instance['alias']
            reference_data = instance
            if id in list(live_dashboard):
                if live_dashboard[id] == reference_data:
                    print(f"This dashboard is already created id :{id}, name: {name}")
                    time.sleep(1)
                else:
                    uid = dashboard_recorder[id]['uid']
                    api = dashboard_recorder[id]['api']
                    url = dashboard_recorder[id]['url']
                    name_new = dashboard_recorder[id]['name']
                    delete_dashboard(uid, api, url ,name_new)
                    dashboard_recorder.pop(id, None)
                    live_dashboard.pop(id, None)
                    time.sleep(1)
                    try:
                        manifest = create_manifest(instance)
                        print("Manifest Created Successfully")
                        with open("manifest.json", 'w') as f:
                            json.dump(manifest, f, indent=2)
                        time.sleep(1)
                        try:
                            config_data = converter(manifest, id, name)
                            print("Config Created")
                            time.sleep(1)
                            try:
                                config_data, api_key = fill_API(config_data)
                                print("API Filled")
                                time.sleep(1)
                                try:
                                    for_api = dynamic(config_data)
                                    live_dashboard[id] = reference_data
                                    dashboard_recorder[id] = {
                                        'uid' : for_api['uid'],
                                        'api' : api_key,
                                        'url' : "http://dev2.virnao.com:3000",
                                        'name' : name
                                    }
                                    time.sleep(1)

                                except:
                                    print("Sorry the dashboard for this config data, couldn't be created because the current version is not compatible.")
                                    time.sleep(1)
                            except:
                                print("API creation failed")
                        except:
                            print("Config Failed")

                    except:
                        print("Manifest Creation Failed")
            else:
            
                try:
                    manifest = create_manifest(instance)
                    print("Manifest Created Successfully")
        
    
                    time.sleep(1)
                    with open("manifest.json", 'w') as f:
                        json.dump(manifest, f, indent=2)
                    
                    
                    try:
                   
                        config_data = converter(manifest, id, name)
                        print("Config Created")
                        time.sleep(1)
                        try:
                            config_data, api_key = fill_API(config_data)
                            print("API Filled")
                            
                            time.sleep(1)
                            try:
                                for_api = dynamic(config_data)
                              
                                live_dashboard[id] = reference_data
                                
                                dashboard_recorder[id] = {
                                    'uid' : for_api['uid'],
                                    'api' : api_key,
                                    'url' : "http://dev2.virnao.com:3000",
                                    'name' : name
                                }
                                time.sleep(1)
                                try: 
                                    dispatch(config_data)
                                    print("Data Dispatched")
                                except:
                                    print("Dispatch Failed")
                                
                            except:
                                print("Sorry the dashboard for this config data, couldn't be created because the current version is not compatible.")
                        except:
                            print("API creation failed")
                    except:
                        print("Config Failed")

                except:
                    print("Manifest Creation Failed")
            time.sleep(1)

            response_fetched[id] = instance
        
        
        # for dashboard not in the current response
        for id in list(live_dashboard):
            if id not in response_fetched:
                uid = dashboard_recorder[id]['uid']
                api = dashboard_recorder[id]['api']
                url = dashboard_recorder[id]['url']
                name_new = dashboard_recorder[id]['name']
                delete_dashboard(uid, api, url, name_new)
                time.sleep(1)
                live_dashboard.pop(id, None)
                dashboard_recorder.pop(id, None)


        
        
    
        print("One iteration complete")
        time.sleep(5)

main()

                    






        