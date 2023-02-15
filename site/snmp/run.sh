#! /bin/bash
cd home
export PATH=$PATH:/usr/local/go/bin

echo "!!    Read Environment Variables build SNMP generator.yml file"
python3 fill_template.py

echo "!!    Run dynamic_start.sh"
./dynamic_start.sh