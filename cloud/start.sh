#! /bin/bash

echo "!!    Make sure Port 3000, 9090, 9091, 9469 are not in use"
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 3000"
sudo lsof -i -P -n | grep 3000
echo "!!    Check Port 9090"
sudo lsof -i -P -n | grep 9090
echo "!!    Check Port 9091"
sudo lsof -i -P -n | grep 9091
echo "!!    Check Port 9469"
sudo lsof -i -P -n | grep 9469

echo "!!    Remove previous stack"
docker stack rm could
echo "!!    Previous stack revmoed"

echo "!!    Start Grafana-server"
sudo systemctl start grafana-server

read -r -p "Config file [config.yml/Enter]: " config_file
read -r -p "Generate Grafana Dashboar? [y/N enter]: " grafana

if [ "$config_file" == "" ]; then
    echo "!!    config.yml"
    echo "!!    Parsing config.yml"
    python3 parse_config.py
    sleep 0.2
    if [ "$grafana" == "y" ] || [ "$grafana" == "Y" ]; then
        cd ..
        cd PrometheusGrafana
        python3 dynamic.py
    else 
        echo "Skip Grafana Dashboard Generation"
    fi
else 
    echo "!!    $config_file"
    echo "!!    Parsing $config_file"
    python3 parse_config.py $config_file
    sleep 0.2
    if [ "$grafana" == "y" ] || [ "$grafana" == "Y" ]; then
        cd ..
        cd PrometheusGrafana
        python3 dynamic.py $config_file
    else 
        echo "Skip Grafana Dashboard Generation"
    fi
fi

echo "!!    Deploy promethues and pushgateway"
docker stack deploy -c docker-stack.yml cloud

sleep 0.2
echo "!!    Deploy script exporter"
yes | cp -rfa se_config/. script_exporter/examples