#! /bin/bash
cd home

echo "!!    Run dynamic_start.sh"
./dynamic_start.sh

echo "!!    Start ARP Exporter"

python3 arp_exporter.py