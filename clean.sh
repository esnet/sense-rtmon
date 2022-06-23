#! /bin/bash
echo "!!    Removing related Stack, Containers, Compose"
docker stack rm site
docker rm -f node-exporter snmp-exporter 
# remove compose containers
docker rm -f dynamicdashboard-snmp-exporter-1 dynamicdashboard-node-exporter-1
# docker image rm -f quay.io/prometheus/node-exporter prom/snmp-exporter
echo "!!    Cleanning Complete"