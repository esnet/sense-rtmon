#! /bin/bash
echo "!!    Delete Cloud Stack"
docker stack rm cloud
echo "!!    Wait for 2s for the containers to shut down"
