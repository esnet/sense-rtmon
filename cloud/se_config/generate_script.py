#!/usr/bin/env python3

import os
import json
import sys
import requests
import re
import yaml

def check_pattern(url, pattern):
    response = requests.get(url)
    content = response.text
    return bool(re.search(pattern, content))

def check_arp(pushgateway, host_names,ips):
    arp_str =""
    for name,ip in zip(host_names,ips):
        name = name.replace("-", "_").replace(".", "_").lower()
        # check if ARP exporters are on
        i = 1
        arp_str = arp_str + f'''
        if curl {pushgateway} | grep '.*arp_state.*instance="{name}".*'; then
            echo "{name}_script_exporter_task{i}{{host="{name}"}} 1"
        else
            echo "{name}_script_exporter_task{i}{{host="{name}"}} 0"
        fi
        '''
        i += 1
        arp_str = arp_str + f'''
        if curl {pushgateway} | grep '.*arp_state.*IPaddress="{ip}".*instance="{name}".*'; then
            echo "{name}_script_exporter_task{i}{{host="{name}"}} 1"
        else
            echo "{name}_script_exporter_task{i}{{host="{name}"}} 0"
        fi
        '''
        
    return arp_str
        
def check_snmp_on(pushgateway,switch_name,job):
    snmp_str = ""
    switch_name = switch_name.replace("-", "_").replace(".", "_").lower()
    snmp_str = snmp_str + f'''
    if curl {pushgateway} | grep '.*ifHCInOctets.*instance="{switch_name}".*job="{job}".*'; then
        echo "{switch_name}_script_exporter_task1{{host="{switch_name}"}} 1"
    else
        echo "{switch_name}_script_exporter_task1{{host="{switch_name}"}} 0"
    fi
    '''
    return snmp_str

def get_mac_from_pushgateway(url, hostname, ip_address):
    response = requests.get(url)
    content = response.text
    
    # Find the line containing both hostname and ip_address
    pattern = fr'.*hostname="{hostname}".*ip_address="{ip_address}".*'
    matched_line = re.search(pattern, content)
    
    if matched_line:
        line = matched_line.group()
        
        # Extract the value of the mac_address field
        mac_address_pattern = r'mac_address="(.*?)"'
        mac_address_match = re.search(mac_address_pattern, line)
        
        if mac_address_match:
            return mac_address_match.group(1)
    
    return None

# def check_snmp_mac(mac_source1,mac_source2,mac1,mac2):
#     sources = [mac_source1, mac_source2]
#     macs = [mac1, mac2]
#     for i,s in enumerate(sources,1):
#         for j,m in enumerate(macs,1):
#             if check_pattern(pushgateway,fr'.*{s}={m.upper()}.*'):
#                 os.system("echo 'switch{i}_host{j}_mac{{host=\"{m}\"}} 1'")
#             else:
#                 os.system("echo 'switch{i}_host{j}_mac{{host=\"{m}\"}} 0'")
def read_yml_file(path, sys_argv, order, go_back_folder_num):
    # locate path
    if path[0] != "/":
        path = "/" + path
    owd = os.getcwd()
    for i in range(go_back_folder_num):
        os.chdir("..")
    config_path = str(os.path.abspath(os.curdir)) + path
    infpth = config_path + "/config.yml"
    os.chdir(owd)
    data = {}
    file_name = "config.yml"

    # argument given
    if len(sys_argv) > 1:
        file_name = str(sys_argv[order])
        file_path = config_path + "/" + file_name
        print(f"\n Config file {file_path}\n")
        with open(file_path, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(f"\n Config file {file_path} could not be found in the config directory\n")
        
    else: # default config file
        with open(infpth, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(f"\n Config file {infpth} could not be found in the config directory\n")
    
    return data,file_name

def main():
    # parse through the config file
    print("\n\nParsing config file...")
    data, config_file = read_yml_file("config_flow", sys.argv, 1, 2)
    pushgateway = f"{data['pushgateway']}/metrics"  # pushgateway metrics page
    with open('l2debugging.sh', 'w') as f:
        f.write('#!/bin/bash \n')
        host_names = []
        ips = []
        for node in data["node"]:
            if node['type'] == 'host':
                host_names.append(node['name'])
                ips.append(node['interface'][0]['ping'])
            if node['type'] == 'switch':
                snmp_str = check_snmp_on(pushgateway, node['name'], node['job'])
                f.write(snmp_str)
            
        arp_str = check_arp(pushgateway, host_names, ips[::-1])
        f.write(arp_str)
    os.system("chmod +x l2debugging.sh")
    # host1_mac = get_mac_from_pushgateway(pushgateway, host2, host1_ip)
    # host2_mac = get_mac_from_pushgateway(pushgateway, host1, host2_ip)

if __name__ == "__main__":    
    main()