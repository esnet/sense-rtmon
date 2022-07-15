#! /bin/bash

# scrape_configs:
#   - job_name: 'script_args'
#     metrics_path: /probe
#     params:
#       script: [args]
#       params: ["arg3,arg4"]
#       arg3: [test3]
#       arg4: [test4]
#     static_configs:
#       - targets: ["localhost:9469"]

echo "!!    args.sh takes in 6 argument"
echo "!!    1. pushgateway's ip address (not localhost)"
echo "!!    2. instance's ip address (where the arp table is located"
echo "!!    3. ip address look up on instance's arp table"
echo "!!    4. number of network elements"
echo "!!    5. network element 1's IP address"
echo "!!    optional 6. if more than one network element input the second one"

# Check ping status
pushgateway=$1
# from which host
host1=$2
# contains which host
host2=$3
# number of network elemenet
switch_num=$4
# network element ip address
switch_ip1=$5
# netowrk element 2 ip address
switch_ip2=$6

####################### ARP Exporter #################################
# get switch 1 mac address 
inter_switch_mac="$(curl ${pushgateway}:9091/metrics | grep \".*ip_address=\"${switch_ip1}\".*\" | awk 'NR==1' 2>/dev/null)"
inter_switch="$(echo \"${inter_switch_mac#*mac_address=\"}\")"
switch1_mac=$(echo ${inter_switch%\}*})
switch1_mac=$(echo ${switch1_mac%\"*})
switch1_mac=$(echo ${switch1_mac#*\"})

# check if ARP exporters are on
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*job=\"arpMetrics\".*"; then
    echo "host1_arp_on{host=\"${host1}\"} 1";
else 
    echo "host1_arp_on{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*job=\"arpMetrics\".*"; then
    echo "host2_arp_on{host=\"${host2}\"} 1";
else 
    echo "host2_arp_on{host=\"${host2}\"} 0";
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

# switch ping check
# if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*ping_switch_status=\"1\".*"; then 
#     echo "host1_ping_switch{host=\"${host1}\"} 1"
# else 
#     echo "host1_ping_switch{host=\"${host1}\"} 0"
# fi
# if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*ping_switch_status=\"1\".*"; then 
#     echo "host2_ping_switch{host=\"${host2}\"} 1"
# else 
#     echo "host2_ping_switch{host=\"${host2}\"} 0"
# fi

# SNMP mac address check switch 1
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*ip_address=\"${switch_ip1}\".*mac_address.*"; then
    echo "host1_snmp_mac_status{host=\"${host1}\"} 1"
    echo "switch1_mac{mac=\"${switch1_mac}\"} ${switch1_mac}"
else 
    echo "host1_snmp_mac_status{host=\"${host1}\"} 0"
fi
if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*ip_address=\"${switch_ip1}\".*mac_address.*"; then
    echo "host2_snmp_mac_status{host=\"${host2}\"} 1"
    echo "switch1_mac{mac=\"${switch1_mac}\"} ${switch1_mac}"
else 
    echo "host2_snmp_mac_status{host=\"${host2}\"} 0"
fi

# ARP IP check
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
# # SNMP mac address check switch 2
# if $switch_num == "2"; then  
#     if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host1}\".*ip_address=\"${switch_ip2}\".*mac_address.*"; then
#         echo "host1_snmp_mac_status2{host=\"${host1}\"} 1"
#     else 
#         echo "host1_snmp_mac_status2{host=\"${host1}\"} 0"
#     fi
#     if curl ${pushgateway}:9091/metrics | grep ".*instance=\"${host2}\".*ip_address=\"${switch_ip2}\".*mac_address.*"; then
#         echo "host2_snmp_mac_status2{host=\"${host2}\"} 1"
#     else 
#         echo "host2_snmp_mac_status2{host=\"${host2}\"} 0"
#     fi
# fi
####################### SMMP Exporter #################################
if curl ${pushgateway}:9091/metrics | grep "dot1.*instance=\"${host1}\".*job=\"snmp-exporter\".*"; then
    echo "host1_snmp_on{host=\"${host1}\"} 1";
else 
    echo "host1_snmp_on{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep "dot1.*instance=\"${host2}\".*job=\"snmp-exporter\".*"; then
    echo "host2_snmp_on{host=\"${host2}\"} 1";
else 
    echo "host2_snmp_on{host=\"${host2}\"} 0";
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
if curl ${pushgateway}:9091/metrics | grep ".*dot1dTpFdbAddress=${host1_mac^^}.*"; then
    echo "switch_host1_mac{host=\"${switch_ip1}\"} 1";
    echo "host1_mac{mac=\"${host1_mac_no_quote}\"} 1"
else 
    echo "switch_host1_mac{host=\"${switch_ip1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep ".*dot1dTpFdbAddress=${host2_mac^^}.*"; then
    echo "switch_host2_mac{host=\"${switch_ip1}\"} 1";
    echo "host2_mac{mac=\"${host2_mac_no_quote}\"} ${host2_mac_no_quote}"
else 
    echo "switch_host2_mac{host=\"${switch_ip1}\"} 0";
fi

####################### NODE Exporter #################################
if curl ${pushgateway}:9091/metrics | grep "go_gc.*instance=\"${host1}\".*job=\"node-exporter\".*"; then
    echo "host1_node_on{host=\"${host1}\"} 1";
else 
    echo "host1_node_on{host=\"${host1}\"} 0";
fi
if curl ${pushgateway}:9091/metrics | grep "go_gc.*instance=\"${host2}\".*job=\"node-exporter\".*"; then
    echo "host2_node_on{host=\"${host2}\"} 1";
else 
    echo "host2_node_on{host=\"${host2}\"} 0";
fi

####################### PAST CODE #################################

# output=$(ping -c 1 "${ip_address}" 2>/dev/null)
# echo "# HELP IP address of target remote host"
# echo "remote_host{ip=\"${ip_address}\"} 1";
# echo "# HELP Number of network elements (e.g. switches) across flow"
# echo "network_element_count" $netElNum
# echo "network_element_ip{ip=\"$netElIP\"}" 1
# echo "# HELP ping_status (0 = failure, 1 = success)";

# if [ $? -eq 0 ]; then
#     # ip=$(printf '%s' "$output" | gawk -F'[()]' '/PING/{print $netElNum}')  
#     echo "# ping to \"${ip_address}\" success";
#     echo "ping_status{host=\"${ip_address}\"} 1";
#     # If success, double check that the MAC address for the other host is in the ARP table
#     echo "# HELP Metric checks whether remote host exists in ARP table of current host";
#     if curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\""; then
#         # DATA=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"")
#         # echo "# \"$DATA\"";
#         echo "arp_status{host=\"${ip_address}\"} 1";
#         # MAC=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | cut -d' ' -f 4);
#         # IFACE=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | cut -d ' ' -f 1 | rev);
#         echo "# HELP MAC Address of Remote Host"
#         echo "remote_host_mac{mac=\"$MAC\"} 1";
#         echo "# HELP Interface of current host which remote host is connected to"
#         echo "remote_host_interface_connect{interface=\"$IFACE\"} 1";

#         if [ $netElNum -eq 1 ]; then
#             echo "# Single Network Element"
#             echo "# HELP Checks whether remote host exists in MAC table of network element";
#             SNMP=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
#             echo "snmp_mac_status{ip=\"$netElIP\"} 1";
#         else 
#             echo "# Multiple Network Element"
#             echo "# HELP Checks whether remote host exists in MAC table of current network element";
#             SNMP1=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
#             echo "snmp_1_mac_status{ip=$netElIP} 1"
#             echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
#             SNMP2=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
#             echo "snmp_2_mac_status{ip=$netElIP2} 0"
#         fi
#     # If not, check the switch's MAC address table
#     else
#         echo "arp_status{host=\"${ip_address}\"} 0"
#         if [ $netElNum -eq 1 ]; then
#             echo "# Single Network Element"
#             echo "# HELP Checks whether remote host exists in MAC table of network element";
#             SNMP=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
#             echo "snmp_mac_status{ip=\"$netElIP\"} 1";
#         else 
#             echo "# Multiple Network Element"
#             echo "# HELP Checks whether remote host exists in MAC table of current network element";
#             SNMP1=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
#             echo "snmp_1_mac_status{ip=$netElIP} 1"
#             echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
#             SNMP2=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
#             echo "snmp_2_mac_status{ip=$netElIP2} 0"
#         fi
#     fi
# else
#     echo "# ping to \"${ip_address}\" failure";
#     echo "ping_status{host=\"${ip_address}\"} 0";
#     # If failure, check if the MAC address for the other host is in the ARP table
#     echo "# HELP Metric checks whether remote host exists in ARP table of current host";
#     if curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\""; then
#         # DATA=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | grep -w \"${ip_address}\")
#         # echo "# \"$DATA\"";
#         echo "arp_status{host=\"${ip_address}\"} 1";
#         # MAC=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | grep -w \"${ip_address}\" | cut -d ' ' -f 4)
#         # IFACE=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | grep -w \"${ip_address}\" | rev | cut -d ' ' -f 1 | rev);
#         echo "# HELP MAC Address of Remote Host"
#         echo "remote_host_mac{mac=\"$MAC\"} 1";
#         echo "# HELP Interface of current host which remote host is connected to"
#         echo "remote_host_interface_connect{interface=\"$IFACE\"} 1";
#     else
#         # If not, check the switch's MAC address table
#         echo "arp_status{host=\"${ip_address}\"} 0"
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
# input=$1
# netElNum=$2
# netElIP=$3
# output=$(ping -c 1 "$input" 2>/dev/null)
# echo "# HELP IP address of target remote host"
# echo "remote_host{ip=\"$input\"} 1";
# echo "# HELP Number of network elements (e.g. switches) across flow"
# echo "network_element_count $netElNum"
# echo "# HELP IP addresses of all network elements across flow"
# echo "network_element_ip $netElIP"
# echo "# HELP ping_status (0 = failure, 1 = success)";
# if [ $? -eq 0 ]; then
#     ip=$(printf '%s' "$output" | gawk -F'[()]' '/PING/{print $2}')  
#     echo "# ping to \"$1\" success";
#     echo "ping_status{host=\"$1\"} 1";
#     # If success, double check that the MAC address for the other host is in the ARP table
#     echo "# HELP Metric checks whether remote host exists in ARP table of current host";
#     if arp -a | grep -w "$input" ; then
#         DATA=$(arp -a | grep -w "$input")
#         echo "# \"$DATA\"";
#         echo "arp_status{host=\"$1\"} 1";
#         MAC=$(arp -a | grep -w "$input" | cut -d' ' -f 4);
#         IFACE=$(arp -a | grep -w "$input" | rev | cut -d ' ' -f 1 | rev);
#         echo "# HELP MAC Address of Remote Host"
#         echo "remote_host_mac{mac=\"$MAC\"} 1";
#         echo "# HELP Interface of current host which remote host is connected to"
#         echo "remote_host_interface_connect{interface=\"$IFACE\"} 1";

#         echo "arp_status{host=\"$1\"} 0"
#         if [ $2 -eq 1 ]; then
#             echo "# Single Network Element"
#             echo "# HELP Metric checks whether remote host exists in MAC table of network element";
#             SNMP=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_mac_status{ip=\"$netElIP\"} 1";
#         else 
#             echo "# Multiple Network Element"
#             echo "# HELP Metric checks whether remote host exists in MAC table of current network element";
#             SNMP1=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_1_mac_status{ip=198.32.43.1} 1$"
#             echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
#             SNMP2=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_2_mac_status{ip=172.16.1.14} 0$"
#         fi
#     # If not, check the switch's MAC address table
#     else
#         echo "arp_status{host=\"$1\"} 0"
#         if [ $2 -eq 1 ]; then
#             echo "# Single Network Element"
#             echo "# HELP Metric checks whether remote host exists in MAC table of network element";
#             SNMP=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_mac_status{ip=\"$netElIP\"} 1";
#         else 
#             echo "# Multiple Network Element"
#             echo "# HELP Metric checks whether remote host exists in MAC table of current network element";
#             SNMP1=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_1_mac_status{ip=198.32.43.1} 1$"
#             echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
#             SNMP2=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_2_mac_status{ip=172.16.1.14} 0$"
#         fi
#     fi
# else
#     echo "# ping to \"$1\" failure";
#     echo "ping_status{host=\"$1\"} 0";
#     # If failure, check if the MAC address for the other host is in the ARP table
#     echo "# HELP Metric checks whether remote host exists in ARP table of current host";
#     if arp -a | grep "$input" ; then
#         DATA=$(arp -a | grep -w "$input")
#         echo "# \"$DATA\"";
#         echo "arp_status{host=\"$1\"} 1";
#         MAC=$(arp -a | grep -w "$input" | cut -d ' ' -f 4)
#         IFACE=$(arp -a | grep -w "$input" | rev | cut -d ' ' -f 1 | rev);
#         echo "# HELP MAC Address of Remote Host"
#         echo "remote_host_mac{mac=\"$MAC\"} 1";
#         echo "# HELP Interface of current host which remote host is connected to"
#         echo "remote_host_interface_connect{interface=\"$IFACE\"} 1";
#     else
#         # If not, check the switch's MAC address table
#         echo "arp_status{host=\"$1\"} 0"
#         if [ $2 -eq 1 ]; then
#             echo "# Single Network Element"
#             echo "# HELP Metric checks whether remote host exists in MAC table of network element";
#             SNMP=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_mac_status{ip=\"$netElIP\"} 1";
#         else 
#             echo "# Multiple Network Element"
#             echo "# HELP Metric checks whether remote host exists in MAC table of current network element";
#             SNMP1=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_1_mac_status{ip=198.32.43.1} 1$"
#             echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
#             SNMP2=$(curl --request GET "http://172.31.72.189:9091/metrics" | grep -w 'dot1dTpFdbEntry\|$netElIP');
#             echo "snmp_2_mac_status{ip=172.16.1.14} 0$"
#         fi
#     fi
# fi
