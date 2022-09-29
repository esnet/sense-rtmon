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
read -r -p "Press Enter to continue: " enter_continue 
read -r -p "Config file [press enter for default choice config_cloud/config.yml]: " config_file
if [ "$config_file" == "" ]; then
    echo "!!    config_cloud/config.yml"
    echo "!!    Parsing config.yml"
    python3 fill_config.py
    sleep 0.2
else 
    echo "!!    $config_file"
    echo "!!    Parsing $config_file"
    python3 fill_config.py $config_file
    sleep 0.2
fi

sleep 1

yes | cp -rfa se_config/. script_exporter/examples
docker stack deploy -c docker-stack.yml cloud

sleep 2

echo "!!    IMPORTANT:"
echo "!!    Before Generating Dashboard for the first time please setup Data Source and Grafana authorization API key"
echo "!!    API key can be done automatically but Data Source needs to be configured MANNUALLY:"
echo "!!    Visit Google Doc for Grafana API and add Promethues as a Data Source "
echo "!!    Instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub"
sleep 2

echo "!!    API Key setup is only needed for the first time"
sleep 1
read -r -p "AUTO setup AUTH API keys? [y/n]: " API 
if [ "$API" == "y" ] || [ "$API" == "Y" ]; then
    # read -r -p "username (default is admin): " username 
    # read -r -p "password (default is admin): " password
    # future iteration feed username and password into curl_api
    python3 fill_API.py
fi 

if [ "$API" != "y" ] || [ "$API" != "Y" ]; then
    echo "!!    APT Key setup instruction:"
    sleep 0.5
    echo "- navigate to <ip_address/domain_name>:3000(or 443 if HTTPS enabled)"
    echo "- login to Grafana with the default authentication (username: admin, password: admin)"
    echo "- setting -> API keys -> add key with Admin permission"
    echo "- copy the API token value starting with 'Bearer ....'"
    echo "- edit any config_cloud/config* files that are used"
    echo "- replace 'CONFIG' in {grafanaAPIToken: 'CONFIG'} with the new API token"
    sleep 1
    echo "!!    Datasource setup instruction:"
    sleep 0.5
    echo "- navigate to <ip_address/domain_name>:3000(or 443 if HTTPS enabled)"
    echo "- login to Grafana with the default authentication (username: admin, password: admin)"
    echo "- setting -> data source -> Promethues -> URL -> Save & Test"
    echo "- enter the IP address NOT DNS"
fi 

sleep 1

read -r -p "Generate Grafana Dashboard? [y/n]: " grafana

if [ "$config_file" == "" ]; then
    if [ "$grafana" == "y" ] || [ "$grafana" == "Y" ]; then
        cd dashboard
        python3 dynamic.py
        cd ..
    else 
        echo "Skip Grafana Dashboard Generation"
        echo "To Generate Dashboard later run ./generate.sh"
    fi
else 
    if [ "$grafana" == "y" ] || [ "$grafana" == "Y" ]; then
        cd dashboard
        python3 dynamic.py $config_file
        cd ..
    else 
        echo "Skip Grafana Dashboard Generation"
        echo "To Generate Dashboard later run ./generate.sh"
    fi
fi

echo "!!    Wait for 3-5 seconds for the containers to get started"
