#!/usr/bin/env bash

pip install pyyaml
pip install prometheus_client
python3 hostMetrics.py hostMetricConfig.yml & ( sleep 2 && python3 json_exporter_arp.py hostMetricConfig.yml )
trap "kill -- -$$" EXIT
