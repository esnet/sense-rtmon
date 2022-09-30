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

sleep 2

echo "!!    Make sure SNMP exporter is running. Dashboard can't be generated without SNMP Exporter"
read -r -p "Config file [press enter for default choice config_cloud/config.yml]: " config_file
if [ "$config_file" == "" ]; then
    echo "!!    config_cloud/config.yml"
    echo "!!    Parsing config.yml"
    python3 prometheus.py
    sleep 0.2
else 
    echo "!!    $config_file"
    echo "!!    Parsing $config_file"
    python3 prometheus.py $config_file
    sleep 0.2
fi

sleep 1

# echo "!!    Transporting Script Exporter configuration files"
# yes | cp -rfa se_config/. script_exporter/examples
# sleep 1

echo "!!    docker stack deployment"
docker stack deploy -c docker-stack.yml cloud

sleep 2

echo "!!    IMPORTANT:"
echo "!!    Before Generating Dashboard for the first time please setup Data Source and Grafana authorization API key"
echo "!!    API key can be done automatically but Data Source needs to be configured MANUALLY:"
echo "!!    Visit Google Doc for Grafana API and add Prometheus as a Data Source "
echo "!!    Instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub"
sleep 3

echo "!!    API Key setup is only needed for the first time"
sleep 1
read -r -p "AUTO setup AUTH API keys? [y/n]: " API 
if [ "$API" == "y" ] || [ "$API" == "Y" ]; then
    python3 fill_API.py
fi 

sleep 1
echo ""
echo ""
echo "!!    Wait for 3-5 seconds for the containers to get started"
echo "!!    Visit grafana through its port (default 300)"
echo "- navigate to http://<ip_address/domain_name>:3000 (or https://<ip_address/domain_name> if HTTPS enabled and port 443 enabled)"
echo "- login to Grafana with the default authentication (username: admin, password: admin)"
sleep 0.5
echo ""
echo "!!    APT Key setup instruction (ignore if API key already setup):"
sleep 0.5
echo "- setting -> API keys -> add key with Admin permission"
echo "- copy the API token value starting with 'Bearer ....'"
echo "- edit any files under /config_flow that are used"
echo "- replace 'CONFIG' in {grafanaAPIToken: 'CONFIG'} with the new API token"
sleep 1
echo ""
echo "!!    Data source setup instruction:"
sleep 0.5
echo "- navigate to <ip_address/domain_name>:3000(or 443 if HTTPS enabled)"
echo "- login to Grafana with the default authentication (username: admin, password: admin)"
echo "- setting -> data source -> Prometheus -> URL -> Save & Test"
echo "- enter the IP address NOT DNS"
sleep 1
echo ""
echo "!!    What's next?"
echo "!!    Flow Generation: run ./generate.sh to generate a dashboard based on the configuration files under config_flow"
echo "!!    Delete Container: run ./clean.sh to remove cloud stack"