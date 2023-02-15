# Cloud Stack (running on a host)

### Step 1 Configuration
- fill out `config.yml` (enables deployment)
- fill out a config file under `config_flow` (enables dashboard generation, skip this step if dashboard is not needed)

### Step 2 Installation
- Run `./install.sh` and follow the steps to install necessary dependencies
- This step includes a encryption process. Follow instructions if certs already exist

### Step 3 Deployment
Run `./start.sh` to deploy `Cloud` stack

### Step 4 Generation a Dashboard
Run `./generate.sh` to generate flows in Grafana

### Cleaning
Run `./clean.sh` to remove all running containers