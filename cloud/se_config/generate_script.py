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

def check_arp_on(pushgateway, host_names,id_name,id):
    arp_str =""
    for name in host_names:
        formatted_name = name.replace("-", "_").replace(".", "_").lower()
        # check if ARP exporters are on
        arp_str = arp_str + f'''
        # check_arp_on
        if curl {pushgateway} | grep '.*arp_state.*' | grep '.*{id_name}="{id}".*' | grep '.*instance="{name}".*' then
            echo '{formatted_name}_script_exporter_task1_{id.replace('-', '_')}{{host="{formatted_name}"}} 1'
        else
            echo '{formatted_name}_script_exporter_task1_{id.replace('-', '_')}{{host="{formatted_name}"}} 0'
        fi
        '''
        
    return arp_str

def check_arp_contain_ip(pushgateway, host_names,ips,id_name,id):
    arp_str =""
    for name,ip in zip(host_names,ips):
        formatted_name = name.replace("-", "_").replace(".", "_").lower()
        arp_str = arp_str + f'''
        # check_arp_contain_ip
        if curl {pushgateway} | grep '.*arp_state.*' | grep '.*{id_name}="{id}".*' | grep '.*instance="{name}".* | grep '.*IPaddress="{ip}".*' then
            echo '{formatted_name}_script_exporter_task2_{id.replace('-', '_')}{{host="{formatted_name}"}} 1'
        else
            echo '{formatted_name}_script_exporter_task2_{id.replace('-', '_')}{{host="{formatted_name}"}} 0'
        fi
        '''
    return arp_str


def get_mac_from_arp(pushgateway, host_names,ips,id_name,id):
    response = requests.get(pushgateway)
    content = response.text
    host_hwadd = []
    for name,ip in zip(host_names,ips):
        pattern = f'.*arp_state.*IPaddress="{ip}".*instance="{name}".*{id_name}="{id}".*'
        match = re.search(pattern, content)
        if match:
            line = match.group(0)

            # Extract the string between 'HWaddress=' and ','
            hwaddress_pattern = r'HWaddress=(.*?),'
            hwaddress_match = re.search(hwaddress_pattern, line)

            if hwaddress_match:
                host_hwadd.append(hwaddress_match.group(1))

    # Reverse the order of the MAC address, as it is stored in reverse order 
    return host_hwadd[::-1]


def check_snmp_on(pushgateway,switch_name,id_name,id):
    snmp_str = ""
    formatted_name = switch_name.replace("-", "_").replace(".", "_").lower()
    snmp_str = snmp_str + f'''
    # check_snmp_on
    if curl {pushgateway} | grep '.*ifHCInOctets.*' | grep '.*instance="{switch_name}.*"' | grep '.*{id_name}="{id}".*'; then
        echo '{formatted_name}_script_exporter_task1_{id.replace('-', '_')}{{host="{formatted_name}"}} 1'
    else
        echo '{formatted_name}_script_exporter_task1_{id.replace('-', '_')}{{host="{formatted_name}"}} 0'
    fi
    '''
    return snmp_str

def check_snmp_mac(pushgateway, switch_names,macs,id_name,id):
    snmp_mac =""
    for name in switch_names:
        formatted_name = name.replace("-", "_").replace(".", "_").lower()
        # check if mac address of both hosts exist on the switch
        for i,mac in enumerate(macs,2):
            snmp_mac = snmp_mac + f'''
            # check_snmp_mac
            if curl {pushgateway} | grep '.*mac_table_info.*' | grep '.*instance="{name}".*' | grep '.*macaddress={mac}.*' | grep '.*{id_name}="{id}".*'; then
                echo '{formatted_name}_script_exporter_task{i}_{id.replace('-', '_')}{{host="{formatted_name}"}} 1'
            else
                echo '{formatted_name}_script_exporter_task{i}_{id.replace('-', '_')}{{host="{formatted_name}"}} 0'
            fi
            '''
            
    return snmp_mac

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
    snmp_str = ""
    arp_str = ""
    # remove http:// or https://
    # before_sep, sep, after_sep = pushgateway.partition("//")
    # pushgateway = after_sep
    with open('l2debugging.sh', 'w') as f:
        f.write('#!/bin/bash \n')
        host_names = []
        switch_names = []
        ips = []
        id_name = "flow"
        id = data['flow']
        for node in data["node"]:
            if node['type'] == 'host':
                host_names.append(node['name'])
                ips.append(node['interface'][0]['ip'])
            if node['type'] == 'switch':
                switch_names.append(node['name'])
                snmp_str = check_snmp_on(pushgateway, node['name'],id_name,id)

        arp_str = check_arp_on(pushgateway, host_names,id_name,id) 
        # host1 contains the ip of host2, vice versa, so we need to reverse the order of ip
        arp_str = arp_str + check_arp_contain_ip(pushgateway, host_names,ips[::-1],id_name,id)

        # host1 contains the ip and mac of host2, vice versa, so we need to reverse the order of ip
        macs = get_mac_from_arp(pushgateway, host_names,ips,id_name,id)
        snmp_str = snmp_str + check_snmp_mac(pushgateway, switch_names,macs,id_name,id)
        f.write(arp_str)
        f.write(snmp_str)

    os.system("chmod +x l2debugging.sh")
    # host1_mac = get_mac_from_pushgateway(pushgateway, host2, host1_ip)
    # host2_mac = get_mac_from_pushgateway(pushgateway, host1, host2_ip)

if __name__ == "__main__":    
    main()