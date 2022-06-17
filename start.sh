#! /bin/bash

echo "!!    Make sure Port 9100, 9116 are not in use"
sleep 1
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 9100 for node exporter"
sudo lsof -i -P -n | grep 9100
sleep 1
echo "!!    Check Port 9116 for snmp exporter"
sudo lsof -i -P -n | grep 9116
sleep 1

# all exporter started
docker stack deploy -c docker-stack.yml site

echo "!!    NODE, SNMP, ARP Exporters (technically everthing already started, shut down one at the time)"

read -r -p "Start Node Exporter [y/N]: " start_node
# shut down node exporter
if [ "$start_node" == "n" ] || [ "$start_node" == "N" ]; then
    echo "Node Exporter removed from the service"
    docker service rm site_node_exporter
else 
    echo "Node Exporter started"
fi

read -r -p "Start SNMP Exporter [y/N]: " start_snmp
if [ "$start_snmp" == "n" ] || [ "$start_snmp" == "N" ]; then
    echo "SNMP Exporter removed from the service"
    docker service rm site_node_exporter
else 
    echo "SNMP Exporter started"
fi