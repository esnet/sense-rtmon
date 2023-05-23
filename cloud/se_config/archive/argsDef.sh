#! /bin/bash

pushgateway=172.31.72.189
# from which host
host1=198.32.43.16
# contains which host
host2=198.32.43.15
# number of network elemenet
switch_num=1
# network element ip address
switch_ip=198.32.43.1

# check if ARP exporters are on
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*"; then
    echo "host1_arp_on{host=\"${host1}\"} 1";
else 
    echo "host1_arp_on{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*"; then
    echo "host2_arp_on{host=\"${host2}\"} 1";
else 
    echo "host2_arp_on{host=\"${host2}\"} 0";
fi

# ARP check
if curl ${pushgateway}:9091/metrics | grep "instance=\"${host1}\",ip_address=\"${host2}\""; then
    echo "host1_has_host2_arp{host=\"${host1}\"} 1";
else 
    echo "host1_has_host2_arp{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep "instance=\"${host2}\",ip_address=\"${host1}\""; then
    echo "host2_has_host1_arp{host=\"${host2}\"} 1";
else 
    echo "host2_has_host1_arp{host=\"${host2}\"} 0";
fi

# ping check
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*ping_status=\"1\".*ping_this_ip=\"${host2}\".*"; then 
    echo "host1_ping_status{host=\"${host1}\"} 1"
else 
    echo "host1_ping_status{host=\"${host1}\"} 0"
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*ping_status=\"1\".*ping_this_ip=\"${host1}\".*"; then 
    echo "host2_ping_status{host=\"${host2}\"} 1"
else 
    echo "host2_ping_status{host=\"${host2}\"} 0"
fi

# SNMP mac address check
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*ip_address=\"${switch_ip}\".*mac_address.*"; then
    echo "host1_snmp_mac_status{host=\"${host1}\"} 1"
else 
    echo "host1_snmp_mac_status{host=\"${host1}\"} 0"
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*ip_address=\"${switch_ip}\".*mac_address.*"; then
    echo "host2_snmp_mac_status{host=\"${host2}\"} 1"
else 
    echo "host2_snmp_mac_status{host=\"${host2}\"} 0"
fi