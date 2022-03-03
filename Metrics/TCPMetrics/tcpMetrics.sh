#!/usr/bin/env bash

sudo yum install tcpdump
pip install pyyaml
pip install prometheus_client
python3 hostMetrics.py hostMetricConfig.yml & ( sleep 2 && python3 json_exporter_tcp.py hostMetricConfig.yml )
trap "kill -- -$$" EXIT
