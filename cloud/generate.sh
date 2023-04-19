#! /bin/bash

echo ""
echo "!!    Available Configuration files under /config_flow, type in one of the below:"
printf "\n"
# echo $(ls ../config_flow/*.yml)
for file in ../config_flow/*.yml; do
  basename "$file"
done
printf "\n"
read -r -p "Enter Configuration File to Generate Dashboards: " config_file
printf "\n"
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

# if [ "${config_file}" == "" ]; then
#     echo "!!    config_flow/config.yml"
#     echo "!!    Parsing config.yml"
#     python3 fill_config.py
#     sleep 0.2
# else 
#     echo "!!    config_flow/${config_file} "
#     echo "!!    Parsing ${config_file} "
#     python3 fill_config.py ${config_file} 
#     sleep 0.2
# fi

if [ "${config_file}" == "" ]; then
    echo "!!    config_flow/config.yml"
    echo "!!    Parsing config.yml"
    # send API
    cd ./orchestrator
    python3 flow_to_api.py config.yml
    cd ..
    # generate script exporter
    cd ./se_config
    python3 generate_script.py
    sleep 0.2
    cd ..
else 
    echo "!!    config_flow/${config_file} "
    echo "!!    Parsing ${config_file} "
    # send API
    cd ./orchestrator
    python3 flow_to_api.py ${config_file}
    cd ..
    # generate script exporter
    cd ./se_config
    python3 generate_script.py ${config_file} 
    sleep 0.2
    cd ..
fi


echo "!!    Transporting Script Exporter configuration files"
yes | cp -rfa se_config/. script_exporter/examples
sleep 1
echo "!! restart script exporter"
# script has been reconfigured, restart script exporter
docker rm -f $(docker ps -a --format "{{.Names}}" | grep "script_exporter")

cd dashboard
if [ "${config_file}" == "" ]; then
    python3 dynamic.py
else 
    python3 dynamic.py ${config_file} 
fi

echo -e "\n"
echo "!!   If you do not see: {id:#, slug: <title>, status: success, uid:<>, url:<title>, version: 1}"
echo "!!   PLEASE RUN ./generate.sh AGAIN, else the dashboards are generated successfully"