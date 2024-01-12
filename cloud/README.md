# Cloud Stack (running on a host)

### Step 1 Configuration
- fill out `config.yml` (enables deployment)
- fill out a config file under `config_flow` (enables dashboard generation, skip this step if dashboard is not needed)
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

### Step 2 Installation
- Run `./install.sh` and follow the steps to install necessary dependencies
- This step includes a encryption process. Follow instructions if certs already exist

### Step 3 Deployment
Run `./start.sh` to deploy `Cloud` stack

### Step 4 Generation a Dashboard
Run `./update.sh` to start generating dashboards.

### Cleaning
Run `./clean.sh` to remove all running containers
