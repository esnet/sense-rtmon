#! /bin/bash
echo "!!    Delete pushgateway and promethues containers"
echo "!!    Stop grafana-server service"
# docker rm -f startpush startprom startgrafana
docker stack rm cloud
sudo systemctl stop grafana-server

echo "!!    Wait for the containers to shut down"
sleep 1.5