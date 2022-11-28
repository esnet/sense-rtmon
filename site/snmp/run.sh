#! /bin/bash
cd home
export PATH=$PATH:/usr/local/go/bin

echo "!!    Read Site Configuration file build SNMP generator.yml file"
python3 fill_template.py config.yml

echo "!!    Read Configuration file build start script"
python3 fill_start.py config.yml

echo "!!    Run dynamic_start.sh"
./dynamic_start.sh