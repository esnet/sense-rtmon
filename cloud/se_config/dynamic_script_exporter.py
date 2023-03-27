#!/usr/bin/env python3

import os
import json
import sys
sys.path.append("..") # Adds higher directory to python modules path.
import cloud_functions
import requests
import re

def check_pattern(url, pattern):
    response = requests.get(url)
    content = response.text
    return bool(re.search(pattern, content))

def check_arp(pushgateway, host1_name, host2_name, ping1, ping2,job):
    host_name = [host1_name, host2_name]
    host_name_rev = [host2_name, host1_name]
    host_ip = [ping1, ping2]
    num = [1, 2]
    num_rev = [2, 1]
    for i,j,name,opposite_name,opposite_ip in zip(num,num_rev,host_name,host_name_rev,host_ip):
        # check if ARP exporters are on
        if check_pattern(pushgateway,fr'.*instance="{name}".*job="{job}".*'):
            os.system("echo 'host{i}_arp_on{{host=\"${name}\"}} 1'")
        else:
            os.system("echo 'host{i}_arp_on{{host=\"${name}\"}} 0'")
        # ping check
        if check_pattern(pushgateway,fr'.*instance="{name}".*ping_status="1".*ping="{opposite_name}".*'):
            os.system("echo 'host{i}_ping_status{{host=\"${name}\"}} 1'")
        else:
            os.system("echo 'host{i}_ping_status{{host=\"${name}\"}} 0'") 
        # ARP IP check, see if the other host is in the ARP table
        if check_pattern(pushgateway,fr'.*instance="{name}".*ip_address="{opposite_ip}".*'):
            os.system("echo 'host{i}_has_host{j}_arp{{host=\"${name}\"}} 1'")
        else:
            os.system("echo 'host{i}_has_host{j}_arp{{host=\"${name}\"}} 0'")   
            
def check_snmp_on(pushgateway, host_num,host_name, job):
    if check_pattern(pushgateway,fr'ifAlias.*instance="{host_name}".*job="{job}".*'):
        os.system("echo 'host{host_num}_arp_on{{host=\"${name}\"}} 1'")
    else:
        os.system("echo 'host{host_num}_arp_on{{host=\"${name}\"}} 0'")

def get_mac_from_pushgateway(url, instance, ip_address):
    response = requests.get(url)
    content = response.text
    
    # Find the line containing both instance and ip_address
    pattern = fr'.*instance="{instance}".*ip_address="{ip_address}".*'
    matched_line = re.search(pattern, content)
    
    if matched_line:
        line = matched_line.group()
        
        # Extract the value of the mac_address field
        mac_address_pattern = r'mac_address="(.*?)"'
        mac_address_match = re.search(mac_address_pattern, line)
        
        if mac_address_match:
            return mac_address_match.group(1)
    
    return None

def check_snmp_mac(mac_source1,mac_source2,mac1,mac2):
    sources = [mac_source1, mac_source2]
    macs = [mac1, mac2]
    for i,s in enumerate(sources,1):
        for j,m in enumerate(macs,1):
            if check_pattern(pushgateway,fr'.*{s}={m.upper()}.*'):
                os.system("echo 'switch{i}_host{j}_mac{{host=\"${m}\"}} 1'")
            else:
                os.system("echo 'switch{i}_host{j}_mac{{host=\"${m}\"}} 0'")

def main():
    # parse through the config file
    print("\n\nParsing config file...")
    data,config_file = cloud_functions.read_yml_file("config_flow",sys.argv,1,2)
    pushgateway = data['pushgateway'] # pushgateway metrics page
    for node in data["node"]:
        if node['type'] == 'host':
            host1 = node['name']
            host1_ip = node['interface'][0]['ip']
            ping1 = node['interface'][0]['ping']
        if node['type'] == 'host' and node['name'] != host1:
            host2 = node['name']
            host2_ip = node['interface'][0]['ip']
            ping2 = node['interface'][0]['ping']
    
    check_arp(pushgateway, host1, host2, ping1, ping2, "arpMetrics")
    check_snmp_on(pushgateway, 1, host1, "snmpMetrics")
    check_snmp_on(pushgateway, 2, host2, "snmpMetrics")
    
    # host1_mac = get_mac_from_pushgateway(pushgateway, host2, host1_ip)
    # host2_mac = get_mac_from_pushgateway(pushgateway, host1, host2_ip)

if __name__ == "__main__":    
    main()