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
input=$1
output=$(ping -c 1 "$input" 2>/dev/null)
echo "# HELP ping_status (0 = failure, 1 = success)";
if [ $? -eq 0 ]; then
    ip=$(printf '%s' "$output" | gawk -F'[()]' '/PING/{print $2}')  
    echo "# ping to \"$1\" success";
    echo "ping_status{host=\"$1\"} 1";
    # If success, double check that the MAC address for the other host is in the ARP table
    echo "# HELP Metric checks whether remote host exists in ARP table of current host";
    echo "# HELP arp_status (0 = failure, 1 = success)";
    if arp -a | grep "$input" ; then
    	DATA=$(arp -a | grep "$input")
    	echo "# \"$DATA\"";
    	echo "arp_status{host=\"$1\"} 1";
    	MAC=$(arp -a | grep "$input" | cut -d' ' -f 4);
    	echo "# HELP MAC Address of Remote Host"
    	echo "remote_host_mac{\"$MAC\"}";
    # If not, check the switch's MAC address table
    else
    	echo "arp_status{host=\"$1\"} 0"
    	# switch=$2
    	# commStrng=$3
    	# echo "# HELP Metric checks whether remote host exists in MAC table of current switch";
    	# echo "# HELP snmp_mac_status (0 = failure, 1 = success)";
    	# if snmpwalk -v 2c -c $commString $switch 1.3.6.1.2.1.17.4.3.1.1 | grep MAC; then
    	# 	SNMP=$(snmpwalk -v 2c -c $commString $switch 1.3.6.1.2.1.17.4.3.1.1 | grep MAC)
    	# 	echo "# \"$SNMP\"";
    	# 	echo "snmp_mac_status{target=\"$2\"} 1";
    	# else 
    	# 	echo "snmp_mac_status{target=\"$2\"} 0";
    	# fi 
    fi
else
    echo "# ping to \"$1\" failure";
    echo "ping_status{host=\"$1\"} 0";
    # If failure, check if the MAC address for the other host is in the ARP table
    echo "# HELP Metric checks whether remote host exists in ARP table of current host";
    echo "# HELP arp_status (0 = failure, 1 = success)";
    if arp -a | grep "$input" ; then
    	DATA=$(arp -a | grep "$input")
    	echo "# \"$DATA\"";
    	echo "arp_status{host=\"$1\"} 1";
    	MAC=$(arp -a | grep "$input" | cut -d' ' -f 4);
    	echo "# HELP MAC Address of Remote Host"
    	echo "remote_host_mac{\"$MAC\"}";
    else
    	# If not, check the switch's MAC address table
    	echo "arp_status{host=\"$1\"} 0"
 		# switch=$2
 		# commStrng=$3
 		# echo "# HELP Metric checks whether remote host exists in MAC table of current switch";
 		# echo "# HELP snmp_mac_status (0 = failure, 1 = success)";
 		# if snmpwalk -v 2c -c $commString $switch 1.3.6.1.2.1.17.4.3.1.1 | grep MAC; then
 		# 	SNMP=$(snmpwalk -v 2c -c $commString $switch 1.3.6.1.2.1.17.4.3.1.1 | grep MAC)
 		# 	echo "# \"$SNMP\"";
 		# 	echo "snmp_mac_status{target=\"$2\"} 1";
 		# else 
 		# 	echo "snmp_mac_status{target=\"$2\"} 0";
 		# fi 
    fi
fi

