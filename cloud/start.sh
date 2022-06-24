#! /bin/bash

echo "!!    Make sure Port 3000, 9090, 9091, 9469 are not in use"
sleep 1
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 3000"
sudo lsof -i -P -n | grep 3000
sleep 1
echo "!!    Check Port 9090"
sudo lsof -i -P -n | grep 9090
sleep 1
echo "!!    Check Port 9091"
sudo lsof -i -P -n | grep 9091
sleep 1
echo "!!    Check Port 9469"
sudo lsof -i -P -n | grep 9469
sleep 1
# sudo docker run -d --name startgrafana -p 3000:3000 -e "GF_INSTALL_PLUGINS=jdbranham-diagram-panel" grafana/grafana
# sudo docker start startgrafana

read -r -p "!!    Input config file name: " config_file

if [ -f "PrometheusGrafana/$config_file" ]; then
    echo "!!    Remove previous stack"
    sleep 0.5
    docker stack rm could
    
    echo "!!    Previous stack revmoed"
    sleep 0.5
    
    echo "!!    Start Grafana-server"
    sudo systemctl start grafana-server
    sleep 1
    
    echo "!!    Deploy promethues and pushgateway"
    docker stack deploy -c docker-stack.yml cloud
    sleep 1
    
    echo "!!    Deploy script exporter"
    cd script_exporter
    docker stack deploy -c docker-compose.yaml cloud
    sleep 1
    
    cd ..
    cd PrometheusGrafana
    # sudo docker run -d --name startprom -p 9090:9090     -v $PWD/prometheus.yml:/etc/prometheus/prometheus.yml     prom/prometheus:v2.2.1
    # sudo docker run -d --name startpush -p 9091:9091 prom/pushgateway
    python3 dynamic.py $config_file

    # read -r -p "Start script exporter? [y/N]: " script

    # if [ "$script" == "y" ] || [ "$script" == "Y" ]; then
        
    # fi
else
    echo "!!    Config file doesn't exist"
    exit 1
fi
