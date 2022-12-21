# Node Exporter

## Container Instructions
- Start Node Exporter: `docker compose up -d` inside `node` directory

### docker-compose.yml
- Pull docker image `zhenboyan/rocky_node_exporter:latest` from Docker Hub
- Node Exporter needs to run on `Host` Mode 
- Environment variables are used for customization, therefore, no configuration needed
- Variable values are per run/site  

### Dockerfile
- Base image: `rockylinux`
- Instal: Go python3 git make wget cronie pip pyyaml
- Github: Prometheus Node Exporter
- File Management: No volume mapping used, all and scripts are wget from this Github repo
- To make changes to the container, edit wget link or change the content in the link and rebuild the image using this Dockerfile

### run.sh
- Entry point of the container
- Set Go into system path
- Run the start script

### dynamic_start.sh
- Crontab: schedule the task to run every 15 seconds
- Task: curl node exporter output to pushgateway server
- Run Node Exporter (official Prometheus Node Exporter from Github)

## Kubernetes Conversion
- kompose used to convert Docker Compose file to Kubernetes files https://kompose.io
- Command used: `kompose convert -f docker-compose.yml` under the parent directory
- Recommended: moving kube files under directory `kubernetes`