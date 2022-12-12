#! /bin/bash
cd home
# export PATH=$PATH:/usr/local/go/bin

echo "!!    Run dynamic_start.sh"
./dynamic_start.sh

echo "!!    Start ARP Exporter"

python3 arp_exporter.py