#! /bin/bash
cd home
echo "!!    Run install.sh"
./install.sh 

echo "!!    Read Configuration file build start script"
fill_start.py config.yml

echo "!!    Run dynamic_start.sh"
./dynamic_start.sh