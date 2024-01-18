import subprocess
import logging
import time
import json
import sys
import requests
import re 
import os
import glob
import datetime
from time import gmtime, strftime
#from converter import orchestratorConvert
from sense.client.workflow_combined_api import WorkflowCombinedApi
from sense.client.discover_api import DiscoverApi
# from generate_s import *
from dynamic import *
# from dispatch import *
from converter import converter
from nodePatch import *
logging.basicConfig(filename='output.log', level=logging.DEBUG)
config = {}
with open("../config_cloud/config.yml", 'r') as f:
    config = yaml.safe_load(f)
try:
    os.system("rm -f api_key.txt")
except:
    print()

try: 
    os.system("rm -f level2/*.sh")
except:
    print()

def fetch_data():
    response = ""
    response = DiscoverApi().discover_service_instances_get()
    try:
        response = DiscoverApi().discover_service_instances_get()
        print("Response Sucessful")
        logging.info("Response Sucessful")
    except:
        logging.critical(f'API Call Failed! Network Error: {response}')
        print("API Call Failed! Network Error")
        
    
    if response == "":
        logging.error("No Data")
       
    
    data = json.loads(response)
    
    return data

def filter_data(data):
    for instance in data['instances']:
        for intent in instance['intents']:
            intent['json'] = json.loads(intent['json'])
    
    filtered_data = [instance for instance in data['instances'] if instance['state'] in ["CREATE - READY", "REINSTATE - READY"]]


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

def fill_API(data, admin, password):
    try:
        with open('api_key.txt', 'r') as file:
            api_key = file.read().strip()
            if api_key:
                data['grafana_api_token'] = "Bearer " + api_key
    except:
        # get time for API keys
      
        now = datetime.datetime.now()
      
        current_time = now.strftime("%m/%d_%H:%M")  

        # curl the API key to here
        curlCMD = "curl -X POST -H \"Content-Type: application/json\" -d '{\"name\":\"" + str(current_time) + f'", "role": "Admin"}}\' http://{admin}:{password}@' + str('http://dev2.virnao.com:3000').split("//")[1] + "/api/auth/keys"
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

    return data , api_key

def generate_dashboard(data):
#     generate_script(data)
#     os.system('yes | cp -rfa se_config/. script_exporter/examples')
#     os.system('yes | docker rm -f $(docker ps -a --format "{{.Names}}" | grep "script_exporter")')
#     dynamic(data)
    pass

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
        logging.info(f"Dashboard uid : {uid}, name: {name}, deleted successfully.")
        return response.json()
    else:
        print(f"Failed to delete dashboard {uid}. Status code: {response.status_code}")
        logging.info(f"Failed to delete dashboard {uid}. Status code: {response.status_code}")
        return None

def main():
    live_dashboard = {}
    dashboard_recorder = {}
    while True:
       
        path_to_sh_files = './level2/'

        sh_files = glob.glob(os.path.join(path_to_sh_files, '*.sh'))

        for sh_file in sh_files:
            print(f"Executing {sh_file}")
            os.system(f'bash {sh_file}')


        # print("Scraping Script Exporter")
        # os.system("./se_config/l2debugging.sh")
        
        if len(live_dashboard) != 0:
            lkj = 1
            print("This are the dashboard right now")
            for id in dashboard_recorder:
                print("\033[32m" + f"{lkj}. Name: {dashboard_recorder[id]['name']}" + "\033[0m")
                lkj += 1
        response_fetched = {}


        try:
            data = fetch_data()
            with open("data_fetch.json", 'w') as f:
                json.dump(data, f, indent=2)
        except:
            logging.error("Failed to fetch data. API Error\nMaking another request in 3 mins.")
            print("Failed to fetch data. API Error\nMaking another request in 3 mins.")
            time.sleep(180)
            continue
        
        #Filter the data || only process the data that are create-ready or reinstate-ready
        try:
            data = filter_data(data)
            with open("data_filtered.json", 'w') as f:
                json.dump(data, f, indent=2)
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
        
        for instance in data:
            id = instance['intents'][0]['json']['service_instance_uuid']
            name = instance['alias']
            reference_data = instance
            if id in list(live_dashboard):
                if live_dashboard[id] == reference_data:
                    print(f"This dashboard is already created id :{id}, name: {name}")
  
                else:
                    uid = dashboard_recorder[id]['uid']
                    api = dashboard_recorder[id]['api']
                    url = dashboard_recorder[id]['url']
                    name_new = dashboard_recorder[id]['name']
                    delete_dashboard(uid, api, url ,name_new)
                    dashboard_recorder.pop(id, None)
                    live_dashboard.pop(id, None)

                    try:
                        manifest = create_manifest(instance)
                        print("Manifest Created Successfully")
                        with open("manifest.json", 'w') as f:
                            json.dump(manifest, f, indent=2)

                        try:
                            config_data = converter(manifest, id, name)
                            print("Config Created")

                            try:
                                config_data, api_key = fill_API(config_data, config['grafana_username'], config['grafana_password'])
                                print("API Filled")
                                
                                
                                

                                try:
                                    for_api = dynamic(config_data, manifest)
                                    live_dashboard[id] = reference_data
                                    dashboard_recorder[id] = {
                                        'uid' : for_api['uid'],
                                        'api' : api_key,
                                        'url' : config['grafana_host'],
                                        'name' : name
                                    }
                                    print("Dashboard Generated")
                                    
                                    try: 
                                        siteMap = node_data(manifest, id, config["pushgateway"])
                                        with open("node_data.json", 'w') as f:
                                            json.dump(siteMap, f, indent = 2)
                                        for idMap in siteMap.keys():
                                            if idMap in config['siterm_url_map']:
                                                baseURL = config['siterm_url_map'][f'{idMap}']
                                                api = SiteRMAPI(baseURL, node_data=siteMap[idMap])
                                                
                                                api.test(siteMap[idMap])
                                            else:
                                                print("\033[32m" + f'This Key: {idMap} does not exist in config.yml'+ "\033[0m")
                                        
                                        print("Data Dispatched")
                                        time.sleep(20)
                                        os.system("python3 ./se_config/generate_script.py flow.yaml")
                                        print("Scraping Script Exporter")
                                        os.system(f"chmod +x level2/{config_data['flow']}.sh")
                                        os.system(f"level2/{config_data['flow']}.sh")
                                    
                                    except:
                                        print("Dispatch Failed")

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
    
                    with open("manifest.json", 'w') as f:
                        json.dump(manifest, f, indent=2)

                    try:
                   
                        config_data = converter(manifest, id, name)
                        print("Config Created")

                        try:
                            config_data, api_key = fill_API(config_data, config['grafana_username'], config['grafana_password'])
                            print("API Filled")
                           
                            with open("converted.json", 'w') as f:
                                json.dump(config_data, f, indent=2)
                            
     
                            try:
                                for_api = dynamic(config_data, manifest)
                              
                                live_dashboard[id] = reference_data
                                
                                dashboard_recorder[id] = {
                                    'uid' : for_api['uid'],
                                    'api' : api_key,
                                    'url' : config['grafana_host'],
                                    'name' : name
                                }
                                print("Dashboard Generated")
                                try: 
                                    siteMap = node_data(manifest, id, config["pushgateway"])
                                    with open("node_data.json", 'w') as f:
                                        json.dump(siteMap, f, indent = 2)
                                    for idMap in siteMap.keys():
                                        if idMap in config['siterm_url_map']:
                                            baseURL = config['siterm_url_map'][f'{idMap}']
                                            api = SiteRMAPI(baseURL, node_data=siteMap[idMap])
                                                
                                            api.test(siteMap[idMap])
                                        else:
                                            print("\033[31m" + f'This Key: {idMap} does not exist in config.yml'+ "\033[0m")
                                    print("Data Dispatched")
                                    time.sleep(20)
                                    os.system("python3 ./se_config/generate_script.py flow.yaml")
                                    print("Scraping Script Exporter")
                                    os.system(f"chmod +x level2/{config_data['flow']}.sh")
                                    os.system(f"level2/{config_data['flow']}.sh")

                                   
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


            
            response_fetched[id] = instance

        
        
        # for dashboard not in the current response
        for id in list(live_dashboard):
            if id not in response_fetched:
                uid = dashboard_recorder[id]['uid']
                api = dashboard_recorder[id]['api']
                url = dashboard_recorder[id]['url']
                name_new = dashboard_recorder[id]['name']
                delete_dashboard(uid, api, url, name_new)
                live_dashboard.pop(id, None)
                dashboard_recorder.pop(id, None)


        
        
 
        time.sleep(10)

main()

                    






        



        


        


        