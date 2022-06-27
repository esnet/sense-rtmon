#! /bin/bash
echo "!!    Removing related Stack, Containers, Compose"
systemctl stop node_exporter
docker stack rm site
docker rm -f node-exporter snmp-exporter arp-exporter tcp-exporter
# remove compose containers
docker rm -f site-node-exporter-1 site-snmp-exporter-1
# docker image rm -f quay.io/prometheus/node-exporter prom/snmp-exporter
docker image rm -f site_tcp-exporter site_arp-exporter arpexporter
echo "!!    Cleanning Complete"