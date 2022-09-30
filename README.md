# sense-rtmon (Dynamic Dashboard)
This package will provide everything needed to install and start `Cloud` and `Site` stack.

## Cloud Stack

### Configuration
- `config.yml` and `multiconfig.yml` files under `config` are configuration examples. 
- `cloud` stack uses config_cloud config files to start docker stack. Dashboards use the config_flow config files.

### Installation
- Run `./install.sh` and follow the steps to install necessary dependencies. 
- The `Cloud` server only needs to execute the installation script inside the cloud directory.

### Running
**NOTE: PLEASE FILL IN CONFIG FILES FIRST BEFORE RUNNING**. All start scripts depend on the configuration file.
- `Cloud` stack consists of Grafana, Prometheus, Pushgateway, and Script Exporter containers. 
- Run `./start.sh` inside `cloud` directory to deploy `Cloud` stack.
- Run `./generate.sh` to generate flows in Grafana.


## Site Stack

### Configuration
- `config.yml` and `multiconfig.yml` files under `config` are configuration examples. 
- `site` stack config files are under config_site.
- To ensure configuration files stay local and no community strings go to the repo run: `git update-index --assume-unchanged config_site/`

### Installation
- Run `./install.sh` and follow the steps to install necessary dependencies. 
- The `site` server only needs to execute the installation script inside the cloud directory.

### Running
**NOTE: PLEASE FILL IN CONFIG FILES FIRST BEFORE RUNNING**. All start scripts depend on the configuration file.
- `site` stack consists of `Node`, `SNMP`, `ARP`, and `TCP` (in development) Exporter. Site stack runs on docker compose instead. 
- Run `./start.sh` inside `site` directory to compose all necessary exporters containers.
- Run `add_switch.py` to add new switch and start a new SNMP exporter.
- RERUN START EVERY TIME CONFIGURATION IS UPDATED. 

## Stopping/Cleaning
- `clean.sh` script under each stack directory removes the running containers.
- Cleaning script under `site` directory offers cleaning URLs on Cloud Servers' pushgateway site.