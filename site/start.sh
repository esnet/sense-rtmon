#! /bin/bash
echo "!!    Please edit config.yml for single switch or multiconfig.yml for multiple switches under DynamicDashboard before procceding"
# read -p "Press enter to continue"

echo "!!    Make sure Port 9100, 9116 are not in use"
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 9100 for node exporter"
sudo lsof -i -P -n | grep 9100
echo "!!    Check Port 9116 for snmp exporter"
sudo lsof -i -P -n | grep 9116

read -r -p "Start Node Exporter? [y/N (Enter)]: " start_node
if [ "$start_node" == "y" ] || [ "$start_node" == "Y" ]; then
    echo "Satring Node Exporter Service"
    docker stack deploy -c node-exporter.yml site
else 
    echo "Skip Node Exporter"
fi

read -r -p "Start SNMP Exporter? [y/N]: " start_snmp
if [ "$start_snmp" == "y" ] || [ "$start_snmp" == "Y" ]; then
    echo "!!    Please configuring switch in snmpConfig.yml if needed"
    echo "!!    DynamicDashboard/SNMPExporter/snmpConfig.yml"
    read -p "Press enter to continue"
    cd ../SNMPExporter
    python3 dynamic.py snmpConfig.yml
    cd ../site
    echo "Satring SNMP Exporter Service"
    docker stack deploy -c snmp-exporter.yml site
else 
    echo "Skip SNMP Exporter"
fi

read -r -p "Start ARP Exporter? [y/N]: " start_arp
if [ "$start_arp" == "y" ] || [ "$start_arp" == "Y" ]; then
    # delete everything first
    read -r -p "Enter host2 IP address (198.32.43.15): " host2IP

    rm -rf ../Metrics/ARPMetrics/jsonFiles ../Metrics/ARPMetrics/arpFiles ../Metrics/ARPMetrics/ping_status ../Metrics/ARPMetrics/update_arp_exporter

    mkdir ../Metrics/ARPMetrics/jsonFiles
    mkdir ../Metrics/ARPMetrics/arpFiles
    mkdir ../Metrics/ARPMetrics/pingStat

    touch ../Metrics/ARPMetrics/arpFiles/arpOut.txt
    touch ../Metrics/ARPMetrics/jsonFiles/arpOut.json
    touch ../Metrics/ARPMetrics/update_arp_exporter.sh
    touch ../Metrics/ARPMetrics/jsonFiles/delete.json
    touch ../Metrics/ARPMetrics/jsonFiles/prev.json
    touch ../Metrics/ARPMetrics/pingStat/ping_status.txt

    chmod +x ../Metrics/ARPMetrics/update_arp_exporter.sh
    sudo tee ../Metrics/ARPMetrics/update_arp_exporter.sh<<EOF
#! /bin/bash
/sbin/arp -a > $general_path/Metrics/ARPMetrics/arpFiles/arpOut.txt
sleep 0.25
python3 $general_path/Metrics/ARPMetrics/convertARP.py $general_path/Metrics/ARPMetrics/arpFiles/arpOut.txt $general_path/Metrics/ARPMetrics/jsonFiles/arpOut.json

ping -c 2 $host2IP
if [ $? -eq 0 ]; then 
  echo "1" > $general_path/Metrics/ARPMetrics/pingStat/ping_status.txt
else
  echo "0" > $general_path/Metrics/ARPMetrics/pingStat/ping_status.txt
fi
EOF
    fi

    echo "Satring ARP Exporter Service"
    cd ../Metrics
    docker image rm -f arp_exporter:latest
    docker build -t arp_exporter -f arp.Dockerfile .
    cd ../site
    docker compose -f arp-exporter.yml up -d
else 
    echo "Skip ARP Exporter"
fi

read -r -p "Start TCP Exporter? [y/N]: " start_tcp
if [ "$start_tcp" == "y" ] || [ "$start_tcp" == "Y" ]; then
    echo "Satring TCP Exporter Service"
    cd ../Metrics
    docker image rm -f tcp_exporter:latest
    docker build -t tcp_exporter -f tcp.Dockerfile .
    cd ../site
    docker compose -f tcp-exporter.yml up -d
else 
    echo "Skip TCP Exporter"
fi

# echo "!!    to start any exporter later, enter:"
# echo "docker stack deploy -c node-exporter.yml site"
# echo "docker stack deploy -c snmp-exporter.yml site"
# echo "!!    Please configuring switch in snmpConfig.yml if needed"
# echo "!!    DynamicDashboard/SNMPExporter/snmpConfig.yml"
# echo "docker stack deploy -c arp-exporter.yml site"
# echo "docker stack deploy -c tcp-exporter.yml site"

echo "!!    to remove site stack run ./clean.sh"
