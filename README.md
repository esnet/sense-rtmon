# sense-rtmon (Dynamic Dashboard)
This package will provide everything needed to run `cloud` and `site` stack.

## Cloud Stack (running on host)

### Configuration
- fill out `config.yml` under `config_cloud` to deploy `cloud stack`.
- `cloud` stack uses config_cloud config files to start docker stack. Dashboards use the config_flow config files.
- Example (config.yml)
- ```yml
  ###### CONFIG YAML ######
  hostIP: H.O.S.T.I.P.
  
  ssl_certificate_key: 'path/to/key'
  ssl_certificate: 'path/to/certificate'
  grafana_host: 'http://dev2.virnao.com:3000'
  pushgateway: 'http://dev2.virnao.com:9091'
  grafana_username: 'username'
  grafana_password: 'password'
  grafana_api_token: "API KEY"
  siterm_url_map:
    "urn:ogf:network:nrp-nautilus.io:2020": https://sense-prpdev-fe.sdn-lb.ultralight.org/T2_US_SDSC/sitefe/json/frontend
    "urn:ogf:network:ultralight.org:2013": https://sense-caltech-fe.sdn-lb.ultralight.org/T2_US_Caltech_Test/sitefe/json/frontend
    "urn:ogf:network:sc-test.cenic.net:2020": https://sense-ladowntown-fe.sdn-lb.ultralight.org/NRM_CENIC/sitefe/json/frontend
  ```
- It also needs auth files
    - /root/.sense-o-auth.yaml
    - /etc/letsencrypt/live/dev2.virnao.com/privkey.pem
    - /etc/letsencrypt/live/dev2.virnao.com/cert.pem

### Installation
- Run `./install.sh` and follow the steps to install necessary dependencies. 

### Running
- `Cloud` stack consists of Grafana, Prometheus, Pushgateway, and Script Exporter containers. 
- Run `./start.sh` to deploy `Cloud` stack.
- Run `./update.sh` to start generating dashboards.

### Cleaning
- `clean.sh` script to removes running containers.

## Site Stack (containerized)

### Configuration
- `site` stack doesn't use any configuration files.
- Configuration is done inside each exporter's `docker-compose.yml` file. Variables are passed in under `environment` session. 

### Installation
- Docker Images are pull from DockerHub.
- To build images run `docker build . -t <user_name>/rocky_<exporter_name>_exporter:latest` under the correct directory. 

### Running
**NOTE: PLEASE FILL IN CONFIG FILES FIRST BEFORE RUNNING**. 
- `site` stack consists of `Node`, `SNMP`, `ARP`, and `TCP` (in development) Exporter.
- Start Exporters: `docker compose up -d` under the exporter directory.
- Detailed instruction can be found under each exporter's directory.

### Stopping
- Stop docker containers either `docker rm <container_id>` or run `docker compose down -v` under exporters' directory.
- Delete pod on cluster: `kubectl delete -n <namespace> deployment <name_of_exporter>-exporter`
