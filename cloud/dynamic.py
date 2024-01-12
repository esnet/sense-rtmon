import subprocess
import os
import json
import re
from datetime import datetime
import sys
import time
import requests
def clean_string(s):
    # This regex looks for a pattern where there are three digits (\d{3})
    # followed by a hyphen (-), and then an alphabetic character ([a-zA-Z])
    pattern = r'\d{3}_[a-zA-Z]'
    
    # Find the position where this pattern occurs
    match = re.search(pattern, s)
    if match:
        # Find the index of the hyphen
        index = match.start() + 3
        # Return the string up to the hyphen
        return s[:index]
    else:
        # If the pattern is not found, return the original string
        return s

def clean_iface(s):
    # This regex looks for a pattern where there are three digits (\d{3})
    # followed by a hyphen (-), and then an alphabetic character ([a-zA-Z])
    pattern = r'\d{3}-[a-zA-Z]'
    
    # Find the position where this pattern occurs
    match = re.search(pattern, s)
    if match:
        # Find the index of the hyphen
        index = match.start() + 3
        # Return the string up to the hyphen
        return s[:index]
    else:
        # If the pattern is not found, return the original string
        return s
    
def generate_mermaid(manifest):
    graph_template = "graph TB\n"
    connections = []

    # Helper function to format node names
    def format_name(name):
        return name.replace(" ", "_").replace(":", "_").replace("/", "_").replace('-', '_')

    # Identify unique hosts and switches
    hosts = {}
    switches = {}
    for port in manifest["Ports"]:
        node_name = format_name(port["Node"])
        port_name = format_name(port["Name"])


        if "Host" in port:
            for host in port["Host"]:
                host_node = port["Node"].replace(":", "_")
                host_interface = host["Interface"]
                host_ip = host["IPv4"]
                host_name = format_name(host["Name"].split(":")[0])

                # Store host information
                hosts[host_name] = (host_interface, host_ip, host_node)
                
        else:
            # It's a switch
            if node_name not in switches:
                switches[node_name] = []
            switches[node_name].append(port_name)
            print(node_name, port_name)

    # Create subgraphs for hosts
    host_graphl = {}
    for host_name, (interface, ip, node_name) in hosts.items():
        host_graphl[f'{interface}_IP'] = node_name
        graph_template += f'''
    subgraph "HOST {host_name}"
        {interface}("{interface}") 
        {interface}_IP("IP: {ip}")
    end
    {interface} --> {interface}_IP
        '''

    # Create subgraphs for switches
    for switch_name, ports in switches.items():
        graph_template += f'\n    subgraph "{switch_name}"\n'
        for port in ports:
            graph_template += f'        {port}("{port}")\n'

        graph_template += '    end\n'

    # Determine switch-to-switch connections from the manifest
    for port in manifest["Ports"]:
        if "Peer" in port and port["Peer"] != "?peer?":
            port_name = format_name(port["Name"])
            peer_port = format_name(port["Peer"].split(":")[-1])
            peer_port = clean_string(peer_port)

            print(port_name, peer_port)
            if (peer_port, port_name) not in connections: # Avoid duplicate connections
                connections.append((port_name, peer_port))

    # Add switch-to-switch connections to the graph
    map_connection = {}

    for port1, port2 in connections:
        if port1 in map_connection or port2 in map_connection:
            continue
        graph_template += f'    {port1} --> {port2}\n'
        map_connection[port1] = port2
        map_connection[port2] = port1
    
    for host_interface in host_graphl:
        switch = switches[host_graphl[host_interface]][0]
        graph_template += f'    {host_interface} --> {switch}\n'

    return graph_template


def api(data, dashboard, manifest):
    url = f"{str(data['grafana_host'])}/api/dashboards/db"
    

    # HTTP Post Header
    # Replace with your Grafana API key
    headers = {"Authorization": str(data['grafana_api_token']), 
            "Content-Type": "application/json",
                "Accept": "application/json"}

    # Open and load out.json input
    f = open(dashboard)
    x = json.load(f)
    
    x['dashboard']['panels'][1]['options']['content'] = generate_mermaid(manifest)

    # HTTP Post Request
    r = requests.post(url=url, headers=headers, data=json.dumps(x), verify=False)
    print(r.json())
    return r.json()


def dynamic(data, manifest):
    lp = data
    if os.path.exists("./dashboard/templates/temp.json"):
        os.remove("./dashboard/templates/temp.json")
        
    def fill_rep(rep,id_num,node=None,iface=None):
        id_num += 1
        rep["ID_UNIQUE"] = unqiue_id.strip()
        rep["UNIQUE_ID_FIELD"] = unique_id_field
        rep["YPOSITION"] = str(id_num)
        rep["PANELID"] = str(id_num)
        if node!=None:
            rep["NODENAME"] = node['name']
            rep["NODETYPE"] = node["type"].capitalize()
        if iface!=None:
            if 'Port' in iface['name']:
                rep["IFNAME"] = clean_iface(iface['name'])
            else:
                rep["IFNAME"] = iface['name'].replace('_', ' ').replace('-', '/')
            rep["IFVLAN"] = iface['vlan']
        return rep,id_num
    
    def replace_file_to_string(file_name,replacements):
        with open(file_name) as file:
            content = file.read()
            for src, target in replacements.items():
                content = content.replace(str(src), str(target))
            return content
    def get_hosts_names(data,rep):
        i = 1
        for n in data["node"]:
            if n["type"] == "host":
                rep[f"HOST{i}NAME"] = n["name"]
                i += 1
        return rep
    
    # concatenate to a json file
    def concat_json(content,output="./dashboard/templates/temp.json",end=False):
        if end == False:
            content = content + ",\n"
        with open(output, 'a') as outfile:
            outfile.write(content) 
    

    def process_dict_list(dict_list):
        result = []
        for item in dict_list:
            item_str = []
            for key, value in item.items():
                if isinstance(value, list):
                    value = ', '.join([f"{k}: {v}" for peer in value for k, v in peer.items()])
                item_str.append(f"{key}: {value}")
            result.append(" | ".join(item_str))
        
        result_str = "\\n".join(result)
        return result_str


    title = f'{data["title"]} |Flow: {data["flow"]}| {datetime.now().strftime("%m/%d_%H:%M")}'
    push_metric = data['pushgateway']
    unique_id_field = "flow" # unique id feild in the template
    unqiue_id = data[unique_id_field] # flow id
    
    

    id_num = 200 # start from 200 in case of conflict with previous panels
    with open("data.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    for node in data["node"]:
        # write node info to a json file

        rep,id_num = fill_rep({},id_num,node)
        info_panel = replace_file_to_string("./dashboard/templates/panel/info_panel.json",rep)
        concat_json(info_panel)

        
        # write interface to a json file
        rep,id_num = fill_rep(rep,id_num)
        rep["INTERFACEINFO"] = process_dict_list(node['interface'])
        interface_panel = replace_file_to_string("./dashboard/templates/panel/interface_panel.json",rep)
        concat_json(interface_panel)
        
        for i,iface in enumerate(node['interface']):
            # special case host without ip address, no monitoring needed
            if 'ip' not in iface and node["type"] == "host":
                continue
            
            # write panel file
            rep,id_num = fill_rep(rep,id_num,node,iface)
            flow_panel = replace_file_to_string("./dashboard/templates/panel/flow_panel.json",rep)
            
            # write target
            target_flow = replace_file_to_string(f"./dashboard/templates/panel/flow_{node['type']}_target.json",rep)

            # write target to panel file
            flow_panel = flow_panel.replace("INSERTTARGET", target_flow)
            concat_json(flow_panel)    
            
            id_num += 1

    
    # L2 debugging tables
    id_num = id_num + 100 # L2 tables start from 100 after flow panels in case of conflict with previous panels
    
    # write node info to a json file
   
    rep,id_num = fill_rep({},id_num)
    unqiue_id = data[unique_id_field].replace('-', '_') # flow id Grafana doesn't like - in raw metrics
    rep["ID_UNIQUE"] = unqiue_id.strip()
    info_panel = replace_file_to_string("./dashboard/templates/l2_debugging_panel/info_panel.json",rep)
    concat_json(info_panel)
    
    for i,node in enumerate(data["node"],i):
        # write table to a temp file
        rep,id_num = fill_rep({},id_num,node)
        l2table = replace_file_to_string("./dashboard/templates/l2_debugging_panel/table.json",rep)
        
        # process filling info
        formatted_name = node['name'].replace("-", "_").replace(".", "_").lower()
        rep = get_hosts_names(data,{})
 
       
        rep["ID_UNIQUE"] = unqiue_id.strip()
        try:
            if node['name'] == rep["HOST1NAME"]:
                rep["OPPOSITENAME"] = rep["HOST2NAME"]
            else :
                rep["OPPOSITENAME"] = rep["HOST1NAME"]
        except:
            try:
                rep["OPPOSITENAME"] = rep["HOST1NAME"]
            except:
                print("This Has no Host Node")
        rep["NODENAME"] = formatted_name
        
        for i in range(1,4):
            rep[f"NODENAME_SCRIPT_EXPORTER_TASK{i}"] = f"{formatted_name}_script_exporter_task{i}"
        node_target = replace_file_to_string(f"./dashboard/templates/l2_debugging_panel/{node['type']}_target.json",rep)
        
        l2table = l2table.replace("INSERTTARGET", node_target)
        concat_json(l2table)
   
    # read the temp file and write to the all general dashboard template
    dashboard_name = f"dash_{data['flow']}.json"
    with open("./dashboard/templates/temp.json") as file:
        all_panels = file.read()
        all_panels = all_panels[:-2] # remove the last comma and newline
        with open("./dashboard/templates/general_dashboard.json") as infile, open(dashboard_name, 'w') as outfile:
            general_content = infile.read()
            general_content = general_content.replace("GRAFANAHOST",data["grafana_host"])
            general_content = general_content.replace("DASHTITLE",title)
            content = general_content.replace("INSERTALLPANELS",all_panels)
            
            outfile.write(content)
    # remove temp file that's no longer needed
    
    
    res = api(data, dashboard_name, manifest)
    if os.path.exists(dashboard_name):
        os.remove(dashboard_name)

    return res

# data = {}
# manifest = {}

# with open("manifest.json", 'r') as f:
#     manifest = json.load(f)
# with open("converted.json", 'r') as f:
#     data = json.load(f)

# dynamic(data, manifest)