#! /bin/bash

read -r -p "Enter configuration file [config.yml (Enter)]: " top_level_config_file
python3 fill.py $top_level_config_file