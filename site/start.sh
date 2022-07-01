#! /bin/bash
echo "!!    Please edit config.yml for single switch or multiconfig.yml for multiple switches under DynamicDashboard before procceding"
read -p "Press enter to continue"

echo "!!    Make sure Port 9100, 9116 are not in use"
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 9100 for node exporter"
sudo lsof -i -P -n | grep 9100
echo "!!    Check Port 9116 for snmp exporter"
sudo lsof -i -P -n | grep 9116

read -r -p "Start Node Exporter? [y/N]: " start_node
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
    echo "Satring ARP Exporter Service"
    cd ../Metrics
    docker image rm -f arp_exporter
    docker build -t arp_exporter -f arp.Dockerfile .
    cd ../site
    docker stack deploy -c arp-exporter.yml site
else 
    echo "Skip ARP Exporter"
fi

read -r -p "Start TCP Exporter? [y/N]: " start_tcp
if [ "$start_tcp" == "y" ] || [ "$start_tcp" == "Y" ]; then
    echo "Satring TCP Exporter Service"
    cd ../Metrics
    docker image rm -f tcp_exporter
    docker build -t tcp_exporter -f tcp.Dockerfile .
    cd ../site
    docker stack deploy -c tcp-exporter.yml site
else 
    echo "Skip TCP Exporter"
fi

echo "!!    to start any exporter later, enter:"
echo "docker stack deploy -c node-exporter.yml site"
echo "docker stack deploy -c snmp-exporter.yml site"
echo "!!    Please configuring switch in snmpConfig.yml if needed"
echo "!!    DynamicDashboard/SNMPExporter/snmpConfig.yml"
echo "docker stack deploy -c arp-exporter.yml site"
echo "docker stack deploy -c tcp-exporter.yml site"

sleep 1

echo "!!    to remove site stack run ./clean.sh"
