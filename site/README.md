# Node Exporter

## Container Instructions
- Start Node Exporter: `docker compose up -d` inside `node` directory
- Configuration file location: `sense-rtmon/config_site/config.yml`

### docker-compose.yml
- Pull docker image `zhenboyan/rocky_node_exporter:latest` from Docker Hub
- Node Exporter needs to run on `Host` Mode 

### Dockerfile
- Base image: `rockylinux`
- Instal: Go python3 git make wget cronie pip pyyaml
- Github: Prometheus Node Exporter
- wget: config_site/config.yml and the three files below
- File Management: No volume mapping used, all data and scripts are wget from this Github repo
- To make changes to the container, edit wget link or change the content in the link and rebuild the image using this Dockerfile

### run.sh
- Entry point of the container
- Set Go into system path
- Read in the configuration file from wget and edit the start script
- Run the start script

### fill_start.py
- Read in pushgateway server and the IP address from the configuration file
- Write the start script accordingly

### dynamic_start.sh
- Crontab: schedule the task to run every 15 seconds
- Task: curl node exporter output to pushgateway server
- Run Node Exporter (official Prometheus Node Exporter from Github)