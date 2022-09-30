#! /bin/bash
read -r -p "Enter Configuration File to Generate Dashboard (file name under config_flow path not needed): " config_file

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

echo "!!    Transporting Script Exporter configuration files"
yes | cp -rfa se_config/. script_exporter/examples
sleep 1

cd dashboard
if [ "$config_file" == "" ]; then
    python3 dynamic.py
else 
    python3 dynamic.py $config_file
fi