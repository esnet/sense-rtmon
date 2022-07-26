#! /bin/bash
echo "!!    Removing related Stack, Containers, Compose"
systemctl stop node_exporter
docker stack rm site
docker compose down -v
docker rm -f node-exporter snmp-exporter arp-exporter tcp-exporter arpexporter tcpexporter
# remove compose containers
docker rm -f site-node-exporter-1 site-snmp-exporter-1 site-arp-exporter-1 site-tcp-exporter-1
# docker image rm -f quay.io/prometheus/node-exporter prom/snmp-exporter
docker image rm -f site_tcp-exporter site_arp-exporter site_tcp-exporter arp_exporter:latest tcp_exporter:latest

rm -rf ./crontabs/push_snmp_exporter_metrics*.sh ./crontabs/push_node_exporter_metrics*.sh 

read -r -p "Erase Metrics [y/N]: " erase
if [ "$erase" == "y" ] || [ "$erase" == "Y" ]; then
    echo "!!    Erase pushgateway urls sent from this host"
    read -r -p "Enter the config file used to start: [config.yml/Enter]: " erase_config
    python3 erase_pushgateway.py erase_config
    echo "!!    Cleanning Complete"
else 
    echo "Nothing Erased"
fi