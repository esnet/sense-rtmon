# sense-rtmon (Dynamic Dashboard)
This package will provide everything needed to install and start `Cloud` and `Site` stack.

## Configuration
- `config.yml` and `multiconfig.yml` files under `config` are configuration examples. 
- Both `Cloud` and `Site` stacks use the same configuration files. In future iterations, this might change to stack-specific.
- To ensure configuration files stay local and no community strings go to the repo run: `git update-index --assume-unchanged config/`
**NOTE: PLEASE FILL IN CONFIG FILES FIRST BEFORE EXECUTING THE BELOW STEPS**. The installation and start scripts depend on the configuration file.

## Installation
- Under `cloud` and `site` stack there's an `install.sh` file. 
- Run `./install.sh` and follow the steps to install necessary dependencies. 
- The `Cloud` server only needs to execute the installation script inside the cloud directory and vice versa.

## Running
- `Cloud` stack consists of Grafana, Prometheus, Pushgateway, and Script Exporter containers. 
- Run `./start.sh` inside `cloud` directory to deploy `Cloud` stack. 
- `Site` stack consists of `Node`, `SNMP`, `ARP`, and `TCP` (in development) Exporter. Site stack runs on docker compose instead. 
- Run `./start.sh` inside `site` directory to compose all necessary exporters containers.
- RERUN START EVERY TIME CONFIGURATION IS UPDATED. 

## Stopping/Cleaning
- `clean.sh` script under each stack directory removes the running containers.
- Cleaning script under `site` directory offers cleaning URLs on Cloud Servers' pushgateway site.