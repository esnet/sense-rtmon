# DynamicDashboard
This package will provide everything needed to install and start `Cloud` and `Site` stack.

## Configuration
- `config.yml` and `multiconfig.yml` files are examples configurations. 
- Both `Cloud` and `Site` stack uses the same configuration files. In future iterations this might change to stack specific configuration file.
- PLEASE FILL IN CONFIG FILES FIRST BEFORE EXECURTING THE BELOW STEPS. The installation and starting scripts depend on the configuration file.

## Installation
- Under `cloud` and `site` stack there's an `install.sh` file. 
- Run `./install.sh` and follow the steps to install necessary dependencies. 
- The `Cloud` server only needs to execute installation script inside the cloud directory and vice versa.

## Running
- `Cloud` stack consists of Grafana, Prometheus, Pushgateway, and Script Exporter containers. 
- Run `./start.sh` inside cloud directory to deploy `Cloud` stack. 
- `Site` stack consists of `Node`, `SNMP`, `ARP`, and `TCP` (in development) Exporter. Site stack runs on docker compose instead. 
- Run `./start.sh` inside site directory to compose all necessary exporters containers.

## Stopping/Cleaning
- `clean.sh` script under each stack directory removes the running containers.
- Cleaning script under `site` directory offers cleaning URLs on Cloud Servers' pushgateway site.