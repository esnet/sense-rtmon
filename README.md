# sense-rtmon (Dynamic Dashboard)
This package will provide everything needed to install and start `Cloud` and `Site` stack.

## Cloud Stack (running on a host)

### Configuration
- `config.yml` and `multiconfig.yml` files under `config` are configuration examples. 
- `cloud` stack uses config_cloud config files to start docker stack. Dashboards use the config_flow config files.

### Installation
- Run `./install.sh` and follow the steps to install necessary dependencies. 
- The `Cloud` server only needs to execute the installation script inside the cloud directory.

### Running
**NOTE: PLEASE FILL IN CONFIG FILES FIRST BEFORE RUNNING**. 
- `Cloud` stack consists of Grafana, Prometheus, Pushgateway, and Script Exporter containers. 
- Run `./start.sh` inside `cloud` directory to deploy `Cloud` stack.
- Run `./generate.sh` to generate flows in Grafana.

### Stopping/Cleaning
- `clean.sh` script under each stack directory removes the running containers.

## Site Stack (completely containerized)

### Configuration
- `site` stack doesn't use any configuration files.
- Configuration is done inside each exporter's `docker-compose.yml` file. Variables are passed in under `environment` session. 

### Installation
- Docker Images are pull from DockerHub.
- To build images run `docker build . -t <user_name>/rocky_<exporter_name>_exporter:latest` under the correct directory 

### Running
**NOTE: PLEASE FILL IN CONFIG FILES FIRST BEFORE RUNNING**. 
- `site` stack consists of `Node`, `SNMP`, `ARP`, and `TCP` (in development) Exporter.
- Start Exporters: `docker compose up -d` under the exporter directory.
- Detailed instruction can be found under each exporter's directory.

### Stopping/Cleaning
- Stop docker containers either `docker rm <container_id>` or run `docker compose down -v` under exporters' directory.