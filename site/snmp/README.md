# SNMP Exporter Container Instructions
- Start Node Exporter: `docker compose up -d` inside `snmp` directory

### docker-compose.yml
- Pull docker image `zhenboyan/rocky_snmp_exporter:latest` from Docker Hub
- Environment variables are used for customization, therefore, no configuration needed
- Variable values are per run/site

### Dockerfile
- Base image: `rockylinux`
- Instal: Go python3 git make wget cronie pip pyyaml
- Github: Prometheus Node Exporter
- wget: the files below
- File Management: No volume mapping used, all scripts are wget from this Github repo
- To make changes to the container, edit wget link or change the content in the link and rebuild the image using this Dockerfile

### run.sh
- Entry point of the container
- Set Go into system path
- Run `fill_template.py` then run `dynamic_start.sh`

### generator_template.yml
- A template to generate `generator.yml` file
- `community string` and `mibs` are fed in from environment variables 

### fill_template.py
- Read in environment variables and write out to `generator.yml` modeled from `generator_template.yml`
- `generator.yml` fed in to generator to make `snmp.yml` that is used to configure `SNMP Exporter`

### dynamic_start.sh
- Crontab: schedule the task to run every 15 seconds
- Task: curl node exporter output to pushgateway server
- Run Node Exporter (official Prometheus Node Exporter from Github)

