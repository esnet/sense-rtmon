#! /bin/bash
cd home

echo "!!    Run dynamic_start.sh"
./dynamic_start.sh

echo "!!    Start TCP Exporter"

python3 tcp_exporter.py