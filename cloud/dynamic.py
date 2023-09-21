import subprocess
import os
import json
import re
from datetime import datetime
import sys
import time
import requests
def generate_mermaid(data):
    # Make Host 1
    host_template = "graph TB\n"
    host=[]
    switch = []
    tag = 65
    delta = 1123

    for node in data['node']:
        if node['type'] == "host":
            template = f"subgraph \"HOST {node['name']}\"\n"
            number = 1
            host1 = []
            for inter in node['interface']:
                text = ""
                try:
                    text = f"IP: {inter['ip']}"
                except:
                    text = f"VLAN: {inter['vlan']}"
                t = f"subgraph \"Interface: {number}\"\n in{tag}({inter['name']}) \n in{delta}({text})\nend\n"
                host1.append(f"in{delta}")
                number += 1
                delta += 1
                tag += 1
                template += t
            template += "end\n"
            host_template += template
            host.append(host1)
        if node['type'] == 'switch':
            template = f"subgraph \"Switch {node['name']}\"\n"
            number = 1
            for inter in node['interface']:
                t = f"subgraph \"Interface: {number}\"\n in{tag}({inter['name']}) \n in{delta}(Vlan: {inter['vlan']})\nend\n"
                switch.append(f"in{delta}")
                number += 1
                delta += 1
                tag += 1
                template += t
            template += "end\n"
            host_template += template

    for i in range(0, len(switch) - 1):
        if i % 2 == 0:
            host_template += f"{switch[i]} -.-> {switch[i + 1]}\n"
        else:
            host_template += f"{switch[i]} --> {switch[i + 1]}\n"
    for i in range(0, len(host)):
        for j in range(0, len(host[i]) - 1):
            host_template += f"{host[i][j]} -.-> {host[i][j + 1]}\n"
    
    try:
        host_template += f"{host[0][1]} --> {switch[0]}\n"
        host_template += f"{switch[len(switch) - 1]} --> {host[1][0]}\n"
    except:
        sys.exit()
    
    return host_template

def api(data, dashboard, lp):
    url = f"{str(data['grafana_host'])}/api/dashboards/db"
    

    # HTTP Post Header
    # Replace with your Grafana API key
    headers = {"Authorization": str(data['grafana_api_token']), 
            "Content-Type": "application/json",
                "Accept": "application/json"}

    # Open and load out.json input
    f = open(dashboard)
    x = json.load(f)
    
    x['dashboard']['panels'][1]['options']['content'] = generate_mermaid(lp)

    # HTTP Post Request
    r = requests.post(url=url, headers=headers, data=json.dumps(x), verify=False)
    print(r.json())
    return r.json()


def dynamic(data):
    lp = data
    if os.path.exists("./dashboard/templates/temp.json"):
        os.remove("./dashboard/templates/temp.json")
        
    def fill_rep(rep,id_num,node=None,iface=None):
        id_num += 1
        rep["ID_UNIQUE"] = unqiue_id
        rep["UNIQUE_ID_FIELD"] = unique_id_field
        rep["YPOSITION"] = str(id_num)
        rep["PANELID"] = str(id_num)
        if node!=None:
            rep["NODENAME"] = node['name']
            rep["NODETYPE"] = node["type"].capitalize()
        if iface!=None:
            rep["IFNAME"] = iface['name']
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
    rep["ID_UNIQUE"] = unqiue_id
    info_panel = replace_file_to_string("./dashboard/templates/l2_debugging_panel/info_panel.json",rep)
    concat_json(info_panel)
    
    for i,node in enumerate(data["node"],i):
        # write table to a temp file
        rep,id_num = fill_rep({},id_num,node)
        l2table = replace_file_to_string("./dashboard/templates/l2_debugging_panel/table.json",rep)
        
        # process filling info
        formatted_name = node['name'].replace("-", "_").replace(".", "_").lower()
        rep = get_hosts_names(data,{})
 
       
        rep["ID_UNIQUE"] = unqiue_id
        if node['name'] == rep["HOST1NAME"]:
            rep["OPPOSITENAME"] = rep["HOST2NAME"]
        else :
            rep["OPPOSITENAME"] = rep["HOST1NAME"]
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
    
    
    res = api(data, dashboard_name, lp)

    return res
            

        

