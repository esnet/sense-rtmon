#! /bin/bash
echo "!!    Delete Cloud Stack"
docker stack rm cloud
echo "!!    Delete Main Loop"
docker rm $(docker stop $(docker ps -a -q --filter ancestor=mainloop))
echo "!!    Wait for 2s for the containers to shut down"
