#! /bin/bash
cd home
export PATH=$PATH:/usr/local/go/bin

# echo "!!    Read Configuration file build start script"
# python3 fill_start.py config.yml

echo "!!    Run dynamic_start.sh"
./dynamic_start.sh