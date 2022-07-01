#!/usr/bin/env bash

pip install pyyaml
pip install prometheus_client
python3 hostMetrics.py & ( sleep 2 && python3 curl_json_exporter_arp.py )
trap "kill -- -$$" EXIT
