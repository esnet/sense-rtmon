#! /bin/bash

pushgateway=172.31.72.189
# from which host
host1=198.32.43.16
# contains which host
host2=198.32.43.15
# number of network elemenet
switch_num=2
# network element ip address
switch_ip1=198.32.43.1
# network element 2 ip address
switch_ip2=172.16.1.14


# check if ARP exporters are on
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*"; then
    echo "m_host1_arp_on{host=\"${host1}\"} 1";
else 
    echo "m_host1_arp_on{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*"; then
    echo "m_host2_arp_on{host=\"${host2}\"} 1";
else 
    echo "m_host2_arp_on{host=\"${host2}\"} 0";
fi

# ARP check
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

# SNMP mac address check switch 1
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*ip_address=\"${switch_ip1}\".*mac_address.*"; then
    echo "m_host1_snmp_mac_status1{host=\"${host1}\"} 1"
else 
    echo "m_host1_snmp_mac_status1{host=\"${host1}\"} 0"
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*ip_address=\"${switch_ip1}\".*mac_address.*"; then
    echo "m_host2_snmp_mac_status1{host=\"${host2}\"} 1"
else 
    echo "m_host2_snmp_mac_status1{host=\"${host2}\"} 0"
fi

# SNMP mac address check switch 2
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*ip_address=\"${switch_ip2}\".*mac_address.*"; then
    echo "m_host1_snmp_mac_status2{host=\"${host1}\"} 1"
else 
    echo "m_host1_snmp_mac_status2{host=\"${host1}\"} 0"
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*ip_address=\"${switch_ip2}\".*mac_address.*"; then
    echo "m_host2_snmp_mac_status2{host=\"${host2}\"} 1"
else 
    echo "m_host2_snmp_mac_status2{host=\"${host2}\"} 0"
fi

# # scrape_configs:
# #   - job_name: 'script_args'
# #     metrics_path: /probe
# #     params:
# #       script: [args]
# #       params: ["arg3,arg4"]
# #       arg3: [test3]
# #       arg4: [test4]
# #     static_configs:
# #       - targets: ["localhost:9469"]

# # Check ping status
# input=198.32.43.15
# netElNum=2
# netElIP=198.32.43.1
# output=$(ping -c 1 "$input" 2>/dev/null)
# echo "# HELP IP address of target remote host"
# echo "m_remote_host{ip=\"$input\"} 1";
# echo "# HELP Number of network elements (e.g. switches) across flow"
# echo "m_network_element_count" $netElNum
# echo "m_network_element_ip_one{ip=\"198.32.43.1\"}" 1
# echo "m_network_element_ip_two{ip=\"172.16.1.14\"}" 1
# echo "# HELP ping_status (0 = failure, 1 = success)";
# if [ $? -eq 0 ]; then
#     ip=$(printf '%s' "$output" | gawk -F'[()]' '/PING/{print $netElNum}')  
#     echo "# ping to \"$input\" success";
#     echo "m_ping_status{host=\"$input\"} 1";
#     # If success, double check that the MAC address for the other host is in the ARP table
#     echo "# HELP Metric checks whether remote host exists in ARP table of current host";
#     if arp -a | grep -w "$input" ; then
#         DATA=$(arp -a | grep -w "$input")
#         echo "# \"$DATA\"";
#         echo "m_arp_status{host=\"$input\"} 1";
#         MAC=$(arp -a | grep -w "$input" | cut -d' ' -f 4);
#         IFACE=$(arp -a | grep -w "$input" | rev | cut -d ' ' -f 1 | rev);
#         echo "# HELP MAC Address of Remote Host"
#         echo "m_remote_host_mac{mac=\"$MAC\"} 1";
#         echo "# HELP Interface of current host which remote host is connected to"
#         echo "m_remote_host_interface_connect{interface=\"$IFACE\"} 1";

#         if [ $netElNum -eq 1 ]; then
#             echo "# Single Network Element"
#             echo "# HELP Checks whether remote host exists in MAC table of network element";
#             SNMP=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "m_snmp_mac_status{ip=\"$netElIP\"} 1";
#         else 
#             echo "# Multiple Network Element"
#             echo "# HELP Checks whether remote host exists in MAC table of current network element";
#             SNMP1=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "m_snmp_1_mac_status{ip=\"198.32.43.1\"} 1"
#             echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
#             SNMP2=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "m_snmp_2_mac_status{ip=\"172.16.1.14\"} 0"
#         fi
#     # If not, check the switch's MAC address table
#     else
#         echo "m_arp_status{host=\"$input\"} 0"
#         if [ $netElNum -eq 1 ]; then
#             echo "# Single Network Element"
#             echo "# HELP Checks whether remote host exists in MAC table of network element";
#             SNMP=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "m_snmp_mac_status{ip=\"$netElIP\"} 1";
#         else 
#             echo "# Multiple Network Element"
#             echo "# HELP Checks whether remote host exists in MAC table of current network element";
#             SNMP1=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "m_snmp_1_mac_status{ip=\"198.32.43.1\"} 1"
#             echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
#             SNMP2=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "m_snmp_2_mac_status{ip=\"172.16.1.14\"} 0"
#         fi
#     fi
# else
#     echo "# ping to \"$input\" failure";
#     echo "m_ping_status{host=\"$input\"} 0";
#     # If failure, check if the MAC address for the other host is in the ARP table
#     echo "# HELP Metric checks whether remote host exists in ARP table of current host";
#     if arp -a | grep "$input" ; then
#         DATA=$(arp -a | grep -w "$input")
#         echo "# \"$DATA\"";
#         echo "m_arp_status{host=\"$input\"} 1";
#         MAC=$(arp -a | grep -w "$input" | cut -d ' ' -f 4)
#         IFACE=$(arp -a | grep -w "$input" | rev | cut -d ' ' -f 1 | rev);
#         echo "# HELP MAC Address of Remote Host"
#         echo "m_remote_host_mac{mac=\"$MAC\"} 1";
#         echo "# HELP Interface of current host which remote host is connected to"
#         echo "m_remote_host_interface_connect{interface=\"$IFACE\"} 1";
#     else
#         # If not, check the switch's MAC address table
#         echo "m_arp_status{host=\"$input\"} 0"
#         # switch=$netElNum
#         # commStrng=$3
#         # echo "# HELP Metric checks whether remote host exists in MAC table of current switch";
#         # echo "# HELP snmp_mac_status (0 = failure, 1 = success)";
#         # if snmpwalk -v 2c -c $commString $switch 1.3.6.1.2.1.17.4.3.1.1 | grep MAC; then
#         #   SNMP=$(snmpwalk -v 2c -c $commString $switch 1.3.6.1.2.1.17.4.3.1.1 | grep MAC)
#         #   echo "# \"$SNMP\"";
#         #   echo "snmp_mac_status{target=\"$netElNum\"} 1";
#         # else 
#         #   echo "snmp_mac_status{target=\"$netElNum\"} 0";
#         # fi 
#     fi
# fi
