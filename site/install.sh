#! /bin/bash

read -r -p "Enter configuration file (press enter to choose default config file /config_site/config.yml or type the config file WITHOUT path): " top_level_config_file
python3 fill_install.py $top_level_config_file

echo "!!    Running the start script that is filled by config.yml file"
sleep 0.5 
./dynamic_install.sh