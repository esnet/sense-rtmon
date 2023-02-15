#! /bin/bash

echo ""
echo "!!    Available Configuration files under /config_flow:"
echo $(ls ../config_flow/)
read -r -p "Enter Configuration File to Generate Dashboards (only the name of the file is needed): " config_file

echo "!!    Make sure SNMP exporter is running. Dashboard can't be generated without at least one SNMP Exporter running."
sleep 0.5

echo "!!    API Key setup is only needed for the first time"
sleep 1
read -r -p "AUTO setup AUTH API keys? [y/n]: " API 
if [ "${API}" == "y" ] || [ "${API}" == "Y" ]; then
    python3 fill_API.py ${config_file} 
    echo ""
    echo "!!    If API key is set up successfully the key is written back to ${config_file} "
    sleep 2
fi 

if [ "${config_file}" == "" ]; then
    echo "!!    config_flow/config.yml"
    echo "!!    Parsing config.yml"
    python3 fill_config.py
    sleep 0.2
else 
    echo "!!    config_flow/${config_file} "
    echo "!!    Parsing ${config_file} "
    python3 fill_config.py ${config_file} 
    sleep 0.2
fi

echo "!!    Transporting Script Exporter configuration files"
yes | cp -rfa se_config/. script_exporter/examples
sleep 1

cd dashboard
if [ "${config_file}" == "" ]; then
    python3 dynamic.py
else 
    python3 dynamic.py ${config_file} 
fi

echo ""
echo ""
echo "!!   If you do not see: {id:#, slug: <title>, status: success, uid:<>, url:<title>, version: 1}"
echo "!!   PLEASE RUN ./generate.sh AGAIN, else the dashboards are generated successfully"