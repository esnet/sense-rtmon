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

# Check ping status
pushgateway=172.31.72.189
# from which host
instance=198.32.43.16
# contains which host
ip_address=198.32.43.15
# number of network elemenet
netElNum=1
# network element ip address
netElIP=198.32.43.1
# network element 2 ip address
netElIP2=172.16.1.14

output=$(ping -c 1 "${ip_address}" 2>/dev/null)

echo "# HELP IP address of target remote host"
echo "remote_host{ip=\"${ip_address}\"} 1";
echo "# HELP Number of network elements (e.g. switches) across flow"
echo "network_element_count" $netElNum
echo "network_element_ip{ip=\"$netElIP\"}" 1
echo "# HELP ping_status (0 = failure, 1 = success)";

if [ $? -eq 0 ]; then
    # ip=$(printf '%s' "$output" | gawk -F'[()]' '/PING/{print $netElNum}')  
    echo "# ping to \"${ip_address}\" success";
    echo "ping_status{host=\"${ip_address}\"} 1";
    # If success, double check that the MAC address for the other host is in the ARP table
    echo "# HELP Metric checks whether remote host exists in ARP table of current host";
    if curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\""; then
        # DATA=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"")
        # echo "# \"$DATA\"";
        echo "arp_status{host=\"${ip_address}\"} 1";
        # MAC=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | cut -d' ' -f 4);
        # IFACE=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | cut -d ' ' -f 1 | rev);
        echo "# HELP MAC Address of Remote Host"
        echo "remote_host_mac{mac=\"$MAC\"} 1";
        echo "# HELP Interface of current host which remote host is connected to"
        echo "remote_host_interface_connect{interface=\"$IFACE\"} 1";

        if [ $netElNum -eq 1 ]; then
            echo "# Single Network Element"
            echo "# HELP Checks whether remote host exists in MAC table of network element";
            SNMP=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
            echo "snmp_mac_status{ip=\"$netElIP\"} 1";
        else 
            echo "# Multiple Network Element"
            echo "# HELP Checks whether remote host exists in MAC table of current network element";
            SNMP1=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
            echo "snmp_1_mac_status{ip=$netElIP} 1"
            echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
            SNMP2=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
            echo "snmp_2_mac_status{ip=$netElIP2} 0"
        fi
    # If not, check the switch's MAC address table
    else
        echo "arp_status{host=\"${ip_address}\"} 0"
        if [ $netElNum -eq 1 ]; then
            echo "# Single Network Element"
            echo "# HELP Checks whether remote host exists in MAC table of network element";
            SNMP=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
            echo "snmp_mac_status{ip=\"$netElIP\"} 1";
        else 
            echo "# Multiple Network Element"
            echo "# HELP Checks whether remote host exists in MAC table of current network element";
            SNMP1=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
            echo "snmp_1_mac_status{ip=$netElIP} 1"
            echo "# HELP snmp_2_mac_status (0 = failure, 1 = success)";
            SNMP2=$(curl --request GET "http://${pushgateway}:9091/metrics" | grep -w "dot1dTpFdbEntry\|$netElIP");
            echo "snmp_2_mac_status{ip=$netElIP2} 0"
        fi
    fi
else
    echo "# ping to \"${ip_address}\" failure";
    echo "ping_status{host=\"${ip_address}\"} 0";
    # If failure, check if the MAC address for the other host is in the ARP table
    echo "# HELP Metric checks whether remote host exists in ARP table of current host";
    if curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\""; then
        # DATA=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | grep -w \"${ip_address}\")
        # echo "# \"$DATA\"";
        echo "arp_status{host=\"${ip_address}\"} 1";
        # MAC=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | grep -w \"${ip_address}\" | cut -d ' ' -f 4)
        # IFACE=$(curl ${pushgateway}:9091/metrics | grep "instance=\"${instance}\",ip_address=\"${ip_address}\"" | grep -w \"${ip_address}\" | rev | cut -d ' ' -f 1 | rev);
        echo "# HELP MAC Address of Remote Host"
        echo "remote_host_mac{mac=\"$MAC\"} 1";
        echo "# HELP Interface of current host which remote host is connected to"
        echo "remote_host_interface_connect{interface=\"$IFACE\"} 1";
    else
        # If not, check the switch's MAC address table
        echo "arp_status{host=\"${ip_address}\"} 0"
        # switch=$netElNum
        # commStrng=$3
        # echo "# HELP Metric checks whether remote host exists in MAC table of current switch";
        # echo "# HELP snmp_mac_status (0 = failure, 1 = success)";
        # if snmpwalk -v 2c -c $commString $switch 1.3.6.1.2.1.17.4.3.1.1 | grep MAC; then
        #   SNMP=$(snmpwalk -v 2c -c $commString $switch 1.3.6.1.2.1.17.4.3.1.1 | grep MAC)
        #   echo "# \"$SNMP\"";
        #   echo "snmp_mac_status{target=\"$netElNum\"} 1";
        # else 
        #   echo "snmp_mac_status{target=\"$netElNum\"} 0";
        # fi 
    fi
fi
