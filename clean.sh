#! /bin/bash

docker stack rm site
docker rm -f node-exporter snmp-exporter
docker image rm -f quay.io/prometheus/node-exporter prom/snmp-exporter