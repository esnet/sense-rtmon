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

echo "!!    Parsing config.yml"
python3 parse_config.py
sleep 0.2

echo "!!    Deploy script exporter"
yes | cp -rfa se_config/. script_exporter/examples

echo "!!    Start Grafana-server"
sudo systemctl start grafana-server

echo "!!    Deploy promethues and pushgateway"
docker stack deploy -c docker-stack.yml cloud

read -r -p "Generate Grafana Dashboar? [y/N enter]: " grafana
if [ "$grafana" == "y" ] || [ "$grafana" == "Y" ]; then
    cd ..
    cd PrometheusGrafana
    read -r -p "Config file [config.yml/Enter]: " config_file
    if [ "$config_file" == "" ]; then
        echo "!!    config.yml"
        python3 dynamic.py
    else 
        echo "!!    $config_file"
        python3 dynamic.py $config_file
    fi
else 
    echo "Skip Grafana Dashboard Generation"
fi

# read -r -p "Start script exporter? [y/N]: " script

# if [ "$script" == "y" ] || [ "$script" == "Y" ]; then

# fi