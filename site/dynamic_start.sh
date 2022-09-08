#! /bin/bash
cd ..
general_path=$PWD
cd ./site


############################# PYTHON SCRIPT FILL OUT ####################
MYIP=
pushgateway_server=
host2IP=
top_level_config_file=
switch_target1=
switch_target2=
############################# PYTHON SCRIPT FILL OUT ####################

echo "!!    Please edit config.yml for single switch or multiconfig.yml for multiple switches under config folder before procceding"
# read -p "Press enter to continue"
echo "!!    Make sure Port 9100, 9116 are not in use"
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 9100 for node exporter"
sudo lsof -i -P -n | grep 9100
echo "!!    Check Port 9116 for snmp exporter"
sudo lsof -i -P -n | grep 9116
# read -r -p "Enter your IP address (e.g. 198.32.43.16): " MYIP
# read -r -p "Enter Pushgateway server IP address (e.g. http://dev2.virnao.com:9091): " pushgateway_server
############################# NODE #############################
read -r -p "Start Node Exporter? [y/N (Enter)]: " start_node
if [ "$start_node" == "y" ] || [ "$start_node" == "Y" ]; then
    starting_node="-f ./compose-files/node-docker-compose.yml" 
    echo "Satring Node Exporter Service"
    > ./crontabs/push_node_exporter_metrics.sh
    chmod +x ./crontabs/push_node_exporter_metrics.sh
    sudo tee ./crontabs/push_node_exporter_metrics.sh<<EOF
#! /bin/bash
curl -s ${MYIP}:9100/metrics | curl --data-binary @- $pushgateway_server/metrics/job/node-exporter/instance/$MYIP
EOF
    # docker stack deploy -c node-exporter.yml site
else
    starting_node=" " 
    echo "Skip Node Exporter"
fi

############################# SNMP #############################
read -r -p "Start SNMP Exporter? [y/N]: " start_snmp
if [ "$start_snmp" == "y" ] || [ "$start_snmp" == "Y" ]; then
    starting_snmp="-f ./compose-files/snmp-docker-compose.yml" 
    starting_snmp2="-f ./compose-files/snmp-docker-compose2.yml" 
    echo "!!    Default starting two SNMP exporters"
    echo "!!    Please configuring switch in you config file (default: config.yml) if needed"
    # read -r -p "Enter the config file: [config.yml/Enter]: " snmp_config
    cd ./SNMPExporter
    python3 dynamic.py $top_level_config_file
    cd ..
    echo "Satring SNMP Exporter Service"
    # docker stack deploy -c snmp-exporter.yml site
    # read -r -p "Enter switch IP :" switchIP
    # read -r -p "Enter VLAN for $switch_target1 seprated by space (e.g. 1000 1001): " VLANA1 VLANA2 VLANA3

    # read -r -p "Second switch [y/N]? " second_switch
    # if [ "$second_switch" == "y" ] || [ "$second_switch" == "Y" ]; then
    #     # read -r -p "Enter switch IP :" switchIP2
    #     # read -r -p "Enter VLAN seprated by space (e.g. 1000 1001): " VLANB1 VLANB2 VLANB3
    # fi
    > ./crontabs/snmp_temp.txt
    > ./crontabs/snmp_temp2.txt
    touch ./crontabs/push_snmp_exporter_metrics.sh
    chmod +x ./crontabs/push_snmp_exporter_metrics.sh
    sudo tee ./crontabs/push_snmp_exporter_metrics.sh<<EOF
#! /bin/bash
if curl ${MYIP}:9116/metrics | grep ".*"; then
    curl -o $general_path/site/crontabs/snmp_temp.txt ${MYIP}:9116/snmp?target=$switch_target1&module=if_mib
    curl -o $general_path/site/crontabs/snmp_temp2.txt ${MYIP}:9117/snmp?target=$switch_target2&module=if_mib
else
    > $general_path/site/crontabs/snmp_temp.txt	
    > $general_path/site/crontabs/snmp_temp2.txt	
fi
cat $general_path/site/crontabs/snmp_temp.txt | curl --data-binary @- $pushgateway_server/metrics/job/snmp-exporter/target_switch/$switch_target1/instance/$MYIP
cat $general_path/site/crontabs/snmp_temp2.txt | curl --data-binary @- $pushgateway_server/metrics/job/snmp-exporter2/target_switch/$switch_target2/instance/$MYIP

EOF

else
    starting_snmp=" "
    starting_snmp2=" " 
    echo "Skip SNMP Exporter"
fi

############################# ARP #############################
read -r -p "Start ARP Exporter? [y/N]: " start_arp
if [ "$start_arp" == "y" ] || [ "$start_arp" == "Y" ]; then
    starting_arp="-f ./compose-files/arp-docker-compose.yml" 
    # delete everything first
    # read -r -p "Enter host2 IP address (e.g. 198.32.43.15): " host2IP

    rm -rf ./Metrics/ARPMetrics/jsonFiles ./Metrics/ARPMetrics/arpFiles ./Metrics/ARPMetrics/pingStat ./crontabs/update_arp_exporter

    mkdir ./Metrics/ARPMetrics/jsonFiles
    mkdir ./Metrics/ARPMetrics/arpFiles
    mkdir ./Metrics/ARPMetrics/pingStat

    touch ./Metrics/ARPMetrics/arpFiles/arpOut.txt
    touch ./Metrics/ARPMetrics/jsonFiles/arpOut.json
    touch ./Metrics/ARPMetrics/jsonFiles/delete.json
    touch ./Metrics/ARPMetrics/jsonFiles/prev.json
    touch ./Metrics/ARPMetrics/pingStat/ping_status.txt
    touch ./Metrics/ARPMetrics/pingStat/prev_ping_status.txt
    
    touch ./crontabs/update_arp_exporter.sh
    chmod +x ./crontabs/update_arp_exporter.sh
    sudo tee ./crontabs/update_arp_exporter.sh<<EOF
#! /bin/bash
/sbin/arp -a > $general_path/site/Metrics/ARPMetrics/arpFiles/arpOut.txt
sleep 0.5
python3 $general_path/site/Metrics/ARPMetrics/convertARP.py $general_path/site/Metrics/ARPMetrics/arpFiles/arpOut.txt $general_path/site/Metrics/ARPMetrics/jsonFiles/arpOut.json
sleep 0.5
ping -c 1 $host2IP
if [ $? -eq 0 ]; then 
  echo "$host2IP/ping_status/1" > $general_path/site/Metrics/ARPMetrics/pingStat/ping_status.txt
else
  echo "$host2IP/ping_status/0" > $general_path/site/Metrics/ARPMetrics/pingStat/ping_status.txt
fi
# sleep 0.5
# ping -c 1 $switchIP
# if [ $? -eq 0 ]; then 
#   echo "$switchIP/switch_ping_status/1" >> $general_path/site/Metrics/ARPMetrics/pingStat/ping_status.txt
# else
#   echo "$switchIP/switch_ping_status/0" >> $general_path/site/Metrics/ARPMetrics/pingStat/ping_status.txt
# fi
EOF
    echo "Satring ARP Exporter Service"
    cd ./Metrics
    docker image rm -f arp_exporter:latest
    docker build -t arp_exporter -f arp.Dockerfile .
    cd ..
    # docker compose -f arp-exporter.yml up -d
else
    starting_arp=" " 
    echo "Skip ARP Exporter"
fi

read -r -p "Start TCP Exporter? [y/N]: " start_tcp
if [ "$start_tcp" == "y" ] || [ "$start_tcp" == "Y" ]; then
    starting_tcp="-f ./compose-files/tcp-docker-compose..yml" 
    echo "Satring TCP Exporter Service"
    cd ./Metrics
    docker image rm -f tcp_exporter:latest
    docker build -t tcp_exporter -f tcp.Dockerfile .
    cd ..
    # docker compose -f tcp-exporter.yml up -d
else
    starting_tcp=" " 
    echo "Skip TCP Exporter"
fi

echo "!!    to remove site stack run ./clean.sh"

echo "docker compose $starting_node $starting_snmp $starting_snmp2 $starting_arp $starting_tcp up -d"
# run nothing
if [ "$starting_node" == " " ] && [ "$starting_snmp" == " " ] && [ "$starting_arp" == " " ] && [ "$starting_tcp" == " " ]; then
    echo "!!    nothing started"
else 
    docker compose $starting_node $starting_snmp $starting_snmp2 $starting_arp $starting_tcp up -d
fi
