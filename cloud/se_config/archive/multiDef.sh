#! /bin/sh
pushgateway=172.31.72.189
host1=10.251.86.10
host2=10.251.86.12
switch_num=2
switch_ip1=172.16.1.1
switch_ip2=132.249.2.46
mac_source1="dot1dTpFdbAddress"
mac_source2="ipNetToMediaPhysAddress"
flow_vlan=""
# above lines are filled in by fill_config.py based on the config file used

echo "!!    args.sh takes in 6 argument"
echo "!!    1. pushgateway's ip address (not localhost)"
echo "!!    2. instance's ip address (where the arp table is located"
echo "!!    3. ip address look up on instance's arp table"
echo "!!    4. number of network elements"
echo "!!    5. network element 1's IP address"
echo "!!    optional 6. if more than one network element input the second one"

####################### ARP Exporter #################################

# check if ARP exporters are on
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*job=\"arpMetrics\".*"; then
    echo "m_host1_arp_on{host=\"${host1}\"} 1";
else 
    echo "m_host1_arp_on{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*job=\"arpMetrics\".*"; then
    echo "m_host2_arp_on{host=\"${host2}\"} 1";
else 
    echo "m_host2_arp_on{host=\"${host2}\"} 0";
fi 

# ping check
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*ping_status=\"1\".*ping_this_ip=\"${host2}\".*"; then 
    echo "m_host1_ping_status{host=\"${host1}\"} 1"
else 
    echo "m_host1_ping_status{host=\"${host1}\"} 0"
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*ping_status=\"1\".*ping_this_ip=\"${host1}\".*"; then 
    echo "m_host2_ping_status{host=\"${host2}\"} 1"
else 
    echo "m_host2_ping_status{host=\"${host2}\"} 0"
fi

# ARP IP check
if curl ${pushgateway}:9091/metrics | grep "instance=\"${host1}\",ip_address=\"${host2}\""; then
    echo "m_host1_has_host2_arp{host=\"${host1}\"} 1";
else 
    echo "m_host1_has_host2_arp{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep "instance=\"${host2}\",ip_address=\"${host1}\""; then
    echo "m_host2_has_host1_arp{host=\"${host2}\"} 1";
else 
    echo "m_host2_has_host1_arp{host=\"${host2}\"} 0";
fi

####################### SMMP Exporter #################################
if curl ${pushgateway}:9091/metrics | grep "ifAlias.*instance=\"${host1}\".*job=\"snmp-exporter\".*target_switch=\"${switch_ip1}\".*"; then
    echo "m_host1_snmp_on_${flow_vlan}{host=\"${host1}\"} 1";
else 
    echo "m_host1_snmp_on_${flow_vlan}{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep "ifAlias.*instance=\"${host2}\".*job=\"snmp-exporter\".*target_switch=\"${switch_ip2}\".*"; then
    echo "m_host2_snmp_on_${flow_vlan}{host=\"${host2}\"} 1";
else 
    echo "m_host2_snmp_on_${flow_vlan}{host=\"${host2}\"} 0";
fi

# get mac address of host 1 and host 2
inter_host1_mac="$(curl ${pushgateway}:9091/metrics | grep \".*instance=\"${host2}\".*ip_address=\"${host1}\".*\" | awk 'NR==1' 2>/dev/null)"
inter1="$(echo \"${inter_host1_mac#*mac_address=\"}\")"
host1_mac=$(echo ${inter1%\}*})
host1_mac_no_quote=$(echo ${host1_mac%\"*})
host1_mac_no_quote=$(echo ${host1_mac_no_quote#*\"})

inter_host2_mac="$(curl ${pushgateway}:9091/metrics | grep \".*instance=\"${host1}\".*ip_address=\"${host2}\".*\" | awk 'NR==1' 2>/dev/null)"
inter2="$(echo \"${inter_host2_mac#*mac_address=\"}\")"
host2_mac=$(echo ${inter2%\}*})
host2_mac_no_quote=$(echo ${host2_mac%\"*})
host2_mac_no_quote=$(echo ${host2_mac_no_quote#*\"})

# find host1 and host2 mac addressed on SNMP metrics from switch
# ^^ makes the mac addresses in upper case. SNMP mac addresses are in uppercase
if curl ${pushgateway}:9091/metrics | grep ".*${mac_source1}=${host1_mac^^}.*"; then
    echo "m_switch1_host1_mac_${flow_vlan}{host=\"${switch_ip1}\"} 1";
    # echo "host1_mac{mac=\"${host1_mac_no_quote}\"} 1"
else 
    echo "m_switch1_host1_mac_${flow_vlan}{host=\"${switch_ip1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep ".*${mac_source1}=${host2_mac^^}.*"; then
    echo "m_switch1_host2_mac_${flow_vlan}{host=\"${switch_ip1}\"} 1";
    # echo "host2_mac{mac=\"${host2_mac_no_quote}\"} 1"
else 
    echo "m_switch1_host2_mac_${flow_vlan}{host=\"${switch_ip1}\"} 0";
fi
# host1 finds its own mac address from switch 2 arp table
# host1 could find its own mac address from its own node exporter
if curl ${pushgateway}:9091/metrics | grep ".*${mac_source2}=${host1_mac^^}.*"; then
    echo "m_switch2_host1_mac_${flow_vlan}{host=\"${switch_ip2}\"} 1";
    # echo "host1_mac{mac=\"${host1_mac_no_quote}\"} 1"
else 
    echo "m_switch2_host1_mac_${flow_vlan}{host=\"${switch_ip2}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep ".*${mac_source2}=${host2_mac^^}.*"; then
    echo "m_switch2_host2_mac_${flow_vlan}{host=\"${switch_ip2}\"} 1";
    # echo "host2_mac{mac=\"${host2_mac_no_quote}\"} 1"
else 
    echo "m_switch2_host2_mac_${flow_vlan}{host=\"${switch_ip2}\"} 0";
fi

####################### NODE Exporter #################################
if curl ${pushgateway}:9091/metrics | grep "go_gc.*instance=\"${host1}\".*job=\"node-exporter\".*"; then
    echo "m_host1_node_on{host=\"${host1}\"} 1";
else 
    echo "m_host1_node_on{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep "go_gc.*instance=\"${host2}\".*job=\"node-exporter\".*"; then
    echo "m_host2_node_on{host=\"${host2}\"} 1";
else 
    echo "m_host2_node_on{host=\"${host2}\"} 0";
fi


# # get switch 1 mac address 
# inter_switch_mac="$(curl ${pushgateway}:9091/metrics | grep \".*ip_address=\"${switch_ip1}\".*\" | awk 'NR==1' 2>/dev/null)"
# inter_switch="$(echo \"${inter_switch_mac#*mac_address=\"}\")"
# switch1_mac=$(echo ${inter_switch%\}*})
# switch1_mac_no_quote=$(echo ${switch1_mac%\"*})
# switch1_mac_no_quote=$(echo ${switch1_mac_no_quote#*\"})