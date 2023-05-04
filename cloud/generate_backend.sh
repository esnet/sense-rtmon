#! /bin/bash
echo "Usage:"
echo "./generate_backend.sh <your path to config file (config_cloud path is extended by default)> "

config_file=$1

if [ "${config_file}" == "" ]; then
    echo ""
    echo "!!    No config file given"
    exit 1
fi

# API Token fetch
python3 fill_API.py ${config_file} 
echo "Step1: "
echo "!!    If you see, API Key: Bearer ....."
echo "!!    API key is set up successfully the key is written back to ${config_file} "

# send API
echo "Step2: "
echo "!!    Parsing ${config_file} "
echo "!!    Sending API request to site rm"
cd ./orchestrator
python3 flow_to_api.py ${config_file}
cd ..

# generate script exporter
echo "Step3: "
echo "!!    Generating script exporter configuration files"
cd ./se_config
python3 generate_script.py ${config_file} 
cd ..
echo "!!    Transporting Script Exporter configuration files"
yes | cp -rfa se_config/. script_exporter/examples
echo "!! restart script exporter"
# script has been reconfigured, restart script exporter
docker rm -f $(docker ps -a --format "{{.Names}}" | grep "script_exporter")

# dashboard generation
echo "Step4: "
echo "!!    Generating Grafana dashboards"
cd dashboard
python3 dynamic.py ${config_file} 

# instruction
echo -e "\n"
echo "!!   If you do not see: {id:#, slug: <title>, status: success, uid:<>, url:<title>, version: 1}"
echo "!!   PLEASE RUN ./generate.sh AGAIN, else the dashboards are generated successfully"