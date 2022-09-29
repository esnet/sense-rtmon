#! /bin/bash
read -r -p "Enter Configuration File to Generate Dashboard (file name under config_cloud path not needed): " config_file

cd dashboard
if [ "$config_file" == "" ]; then
    python3 dynamic.py
else 
    python3 dynamic.py $config_file
fi