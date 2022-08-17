#! /bin/bash
echo "!!    Delete Cloud Stack"
docker stack rm cloud
sudo systemctl stop grafana-server
echo "!!    Wait for 2s for the containers to shut down"
