#! /bin/bash
cd ..
general_path=${PWD}
cd ./site


############################# PYTHON SCRIPT FILL OUT ####################
MYIP=
pushgateway_server=
host2IP=
top_level_config_file=
switch_target1=
switch_target2=
switchNum=
############################# PYTHON SCRIPT FILL OUT ####################

############################# CRONTAB ###################################
echo "!!    Set up crontab only needed when running for the first time"
read -r -p "Set up crontab? [y/n]: " crontab
if [ "${crontab}" == "y" ] || [ "${crontab}" == "Y" ]; then
    echo "Starting Crontab setup"
    # create a temporary copy paste file
    echo ""
    > ./crontabs/cron_autopush
    > ./crontabs/cron_history

    echo "!!    copy paste crontab to a temporary file"
    crontab -l > ./crontabs/cron_autopush
    crontab -l > ./crontabs/cron_history

    # check if job is alread in crontab
    if grep -F "* * * * * for i in 0 1 2; do ${PWD}/crontabs/push_snmp_exporter_metrics.sh & sleep 15; done; ${PWD}/crontabs/push_snmp_exporter_metrics.sh" ./crontabs/cron_autopush 
    then
        echo "exact SNMP task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: snmp exporter send data to pushgateway every 15 seconds" >> ./crontabs/cron_autopush
        echo "MAILTO=""" >> ./crontabs/cron_autopush
        echo "* * * * * for i in 0 1 2; do ${PWD}/crontabs/push_snmp_exporter_metrics.sh & sleep 15; done; ${PWD}/crontabs/push_snmp_exporter_metrics.sh" >> ./crontabs/cron_autopush
    fi

    if grep -F "* * * * * for i in 0 1 2; do ${PWD}/crontabs/push_node_exporter_metrics.sh & sleep 15; done; ${PWD}/crontabs/push_node_exporter_metrics.sh" ./crontabs/cron_autopush
    then    
        echo "exact Node task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: node exporter send data to pushgateway every 15 seconds" >> ./crontabs/cron_autopush
        echo "MAILTO=""" >> ./crontabs/cron_autopush
        echo "* * * * * for i in 0 1 2; do ${PWD}/crontabs/push_node_exporter_metrics.sh & sleep 15; done; ${PWD}/crontabs/push_node_exporter_metrics.sh" >> ./crontabs/cron_autopush
    fi

    if grep -F "* * * * * for i in 0 1 2; do ${PWD}/crontabs/update_arp_exporter.sh & sleep 15; done; ${PWD}/crontabs/update_arp_exporter.sh" ./crontabs/cron_autopush
    then    
        echo "exact ARP task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: check update on arp table every 15 seconds" >> ./crontabs/cron_autopush
        echo "MAILTO=""" >> ./crontabs/cron_autopush
        echo "* * * * * for i in 0 1 2; do ${PWD}/crontabs/update_arp_exporter.sh & sleep 15; done; ${PWD}/crontabs/update_arp_exporter.sh" >> ./crontabs/cron_autopush
    fi

    echo ""
    crontab ./crontabs/cron_autopush
    rm -f ./crontabs/cron_autopush
    echo "!!    crontab set up successfully"
else 
    echo "Skip crontab, crontab is needed to push metrics successfully"
fi
############################# CRONTAB ###################################

echo "!!    Please edit config.yml for single switch or multiconfig.yml for multiple switches under config folder before proceeding"
echo "!!    Make sure Port 9100, 9116 are not in use"
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 9100 for node exporter"
sudo lsof -i -P -n | grep 9100
echo "!!    Check Port 9116 for snmp exporter"
sudo lsof -i -P -n | grep 9116

echo ""
echo "!!    What is this host monitoring?"
echo "1.    Host Only (Start: Node & ARP)"
echo "2.    Host and Switch (Start: Node, ARP & SNMP)"
echo "3.    Switch Only (Start: SNMP)"
echo "!!    Choose the following options accordingly"
echo ""
sleep 1

start_exporters=""
############################# NODE #############################
read -r -p "Start Node Exporter? [y/n]: " start_node
if [ "${start_node}" == "y" ] || [ "${start_node}" == "Y" ]; then
    starting_node="-f ./compose-files/node-docker-compose.yml" 
    start_exporters="${start_exporters} ${starting_node}"
    echo "Starting Node Exporter Service"
    sudo tee ./crontabs/push_node_exporter_metrics.sh<<EOF
#! /bin/bash
curl -s ${MYIP}:9100/metrics | curl --data-binary @- ${pushgateway_server}/metrics/job/node-exporter/instance/${MYIP}
EOF
    chmod 755 ./crontabs/push_node_exporter_metrics.sh
else
    starting_node=" " 
    echo "Skip Node Exporter"
fi

############################# SNMP #############################
read -r -p "Start SNMP Exporter? [y/n]: " start_snmp
if [ "$start_snmp" == "y" ] || [ "$start_snmp" == "Y" ]; then
    starting_snmp="-f ./compose-files/snmp-docker-compose.yml" 
    # depends on the number of switch, fill in the correct number of compose files
    for (( i=1; i < ${switchNum}; ++i ))
    do
        num=$(echo "${i}+1"|bc)
        starting_snmp="${starting_snmp} -f ./compose-files/snmp-docker-compose${num}.yml"
    done
    start_exporters="${start_exporters} ${starting_snmp}"
    echo "!!    Default starting two SNMP exporters"
    echo "!!    Please configuring switch in you config file (default: /config_site/config.yml) if needed"

    echo "Starting SNMP Exporter Service"
    touch ./crontabs/snmp_temp.txt
    touch ./crontabs/push_snmp_exporter_metrics.sh
    chmod 755 ./crontabs/push_snmp_exporter_metrics.sh
    sudo tee ./crontabs/push_snmp_exporter_metrics.sh<<EOF
#! /bin/bash
if curl ${MYIP}:9116/metrics | grep ".*"; then
    curl -o ${general_path}/site/crontabs/snmp_temp.txt ${MYIP}:9116/snmp?target=${switch_target1}&module=if_mib
else
    > ${general_path}/site/crontabs/snmp_temp.txt	
fi
cat ${general_path}/site/crontabs/snmp_temp.txt | curl --data-binary @- ${pushgateway_server}/metrics/job/snmp-exporter/target_switch/${switch_target1}/instance/${MYIP}
EOF
    
    cd ./SNMPExporter
    python3 dynamic.py $top_level_config_file
    cd ..

else
    starting_snmp=" "
    echo "Skip SNMP Exporter"
fi

############################# ARP #############################
read -r -p "Start ARP Exporter? [y/n]: " start_arp
if [ "${start_arp}" == "y" ] || [ "${start_arp}" == "Y" ]; then
    starting_arp="-f ./compose-files/arp-docker-compose.yml" 
    # delete everything first
    start_exporters="${start_exporters} ${starting_arp}"

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
    chmod 755 ./crontabs/update_arp_exporter.sh
    sudo tee ./crontabs/update_arp_exporter.sh<<EOF
#! /bin/bash
/sbin/arp -a > ${general_path}/site/Metrics/ARPMetrics/arpFiles/arpOut.txt
sleep 0.5
python3 ${general_path}/site/Metrics/ARPMetrics/convertARP.py ${general_path}/site/Metrics/ARPMetrics/arpFiles/arpOut.txt ${general_path}/site/Metrics/ARPMetrics/jsonFiles/arpOut.json
sleep 0.5
ping -c 1 ${host2IP}
if [ $? -eq 0 ]; then 
  echo "${host2IP}/ping_status/1" > ${general_path}/site/Metrics/ARPMetrics/pingStat/ping_status.txt
else
  echo "${host2IP}/ping_status/0" > ${general_path}/site/Metrics/ARPMetrics/pingStat/ping_status.txt
fi
EOF
    echo "Starting ARP Exporter Service"
    cd ./Metrics
    docker image rm -f arp_exporter:latest
    docker build -t arp_exporter -f arp.Dockerfile .
    cd ..
else
    starting_arp=" " 
    echo "Skip ARP Exporter"
fi

read -r -p "Start TCP Exporter? [y/n]: " start_tcp
if [ "${start_tcp}" == "y" ] || [ "${start_tcp}" == "Y" ]; then
    starting_tcp="-f ./compose-files/tcp-docker-compose.yml" 
    start_exporters="${start_exporters} ${starting_tcp}"
    echo "Starting TCP Exporter Service"
    cd ./Metrics
    docker image rm -f tcp_exporter:latest
    docker build -t tcp_exporter -f tcp.Dockerfile .
    cd ..
else
    starting_tcp=" " 
    echo "Skip TCP Exporter"
fi


echo "!!    to remove site stack run ./clean.sh"

# STARTING DOCKER CONTAINERS
echo "docker compose ${start_exporters} up -d"
# run nothing
if [ "${starting_node}" == " " ] && [ "${starting_snmp}" == " " ] && [ "${starting_arp}" == " " ] && [ "${starting_tcp}" == " " ]; then
    echo "!!    nothing started"
else 
    docker compose ${start_exporters} up -d
fi
