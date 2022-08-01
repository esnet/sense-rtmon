#! /bin/bash

read -r -p "Enter configuration file [config.yml (Enter)]: " top_level_config_file
python3 fill.py $top_level_config_file

echo "!!    Running the start script that is filled by config.yml file"
sleep 0.5 
./start2