# ARP Exporter

## Container Instructions
- Start Arp Exporter: `docker compose up -d` inside `arp` directory

### docker-compose.yml
- Pull docker image `zhenboyan/rocky_arp_exporter:latest` from Docker Hub
- Arp Exporter needs to run on `Host` Mode 
- Environment variables are used for customization, therefore, no configuration needed
- Variable values are per run/site  

### Dockerfile
- Base image: `rockylinux`
- Instal: Go python3 git make wget cronie pip pyyaml
- File Management: No volume mapping used, all and scripts are wget from this Github repo
- To make changes to the container, edit wget link or change the content in the link and rebuild the image using this Dockerfile

### run.sh
- Entry point of the container
- Set Go into system path
- Run the start script

### dynamic_start.sh
- Crontab: schedule the task to run every 15 seconds
- Task: curl arp exporter output to pushgateway server
- Run ARP Exporter (homemade arp_exporter)

### arp_exporter.py
- Get ARP table with `arp -a`.
- `arp_out.json` stores the output of `arp -a` of the host system in json format (the plain output is converted to json by `convertARP.py`)
- `prev.json` stores the previous `arp -a` output
- `delete.json` stores all current URLs on pushgateway in the format that can be processed to erase pushgateway data directly
- `aro_out.json` is updated every 15s. If there is discrepancy between it and `prev.json`, ARP container deletes all current URLs from `delete.json` files and push new URLs from `arp_out.json`
- `ping_status` and `prev_ping_status` work in a similar fashion. The host pings the other host and stores the result and send it to pushgateway. If the two files are different, delete everything on pushgateway and resend the URLs and ping status.
- All pushes and deletes are done using `requests` library's `post` and `delete`
- `class_arp_exporter.py` functions the same way, but working under a `class` that's less manageable 

## Kubernetes Conversion
- kompose used to convert Docker Compose file to Kubernetes files https://kompose.io
- Command used: `kompose convert -f docker-compose.yml` under the parent directory
- Recommended: moving kube files under directory `kubernetes`