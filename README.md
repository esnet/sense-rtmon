# DynamicDashboard
Custom Scripts for Dynamic End-To-End Flow-Specific Grafana Dashboards

This repository serves as the codebase for a custom script to dynamically generate Grafana dashboards providing end-to-end flow-specific information provided a config file of relevant information.
The custom script has the following functionalities:
- Modifying the layout of the Grafana dashboard dynamically for multiple network elements
- Displaying flow-specific end-to-end information based on the config file information
- Dynamically constructing an SNMP Exporter config file to poll fine-grained OIDs from specific interfaces as specified in the config file
- Automatically turning on/off SNMP Exporter for specific scrape times and durations specified in config file through the SNMP Config File
- Automatically loading JSON files to Grafana via Dashboard HTTP API
- Dynamically generating Prometheus, Grafana, Pushgateway, Node Exporter, and SNMP Exporter Docker containers from base images within the script

## Python Scripts
The scripts that perform the dynamic dashboard generation is ```dynamic.py```. The python script takes in one argument via the command line of a config file containing the necessary details for dashboard generation. 

**Usage:** ```python dynamic.py <config_file>```

## Config File
In this repository, there are multiple sample config files (```bottomFlowConfig.yml```, ```multiRandom.yml```, ```multiSwitchConfig.yml```, ```randomConfig.yml```, ```threeSwitchConfig.yml```, ```topFlowConfig.yml```, ```threeRandom.yml```). 
The config files contain the following information: 
- Host Information:
  - Host IP Address
  - Host Interface Name & IP
  - Host VLAN
  - Host Node Exporter Port
  - Corresponding Switch Interface Name & IP
- Network Element Information
  - Number of Network Elements
  - SNMP Exporter Job Name
  - Network Element IP Address
  - Network Element Interface In/Out Name & IP
  - Network Element SNMP Exporter OIDs

## Supporting Files
In order for the Python scripts to run, it utilizes a set of templating files as supporting files. The following are supporting files required to run various scripts:
  - ```generator.yml```
  - ```generatorTemplate.yml```
  - ```prometheusTemplate.yml```
  - ```template.json```
  - ```template2.json```
  - ```template3.json```
  - ```api.py```

## Configuration

**Step 1:**
Download this repository in a directory with root access (preferrably within the root directory):
- ```git clone -b splitDocker https://github.com/PannuMuthu/DynamicDashboard```

**Step 2:** Configure Grafana as a Docker container. Since the dynamic dashboard script relies on the Grafana API, we must manually generate an API key to provide the script. For all other polling software (Prometheus, Pushgateway, Node Exporter, SNMP Exporter), the script will automatically generate the containers through the base image CLI commands.
- ```docker run -d  --name grafana -p 3000:3000   -e "GF_INSTALL_PLUGINS=jdbranham-diagram-panel"   grafana/grafana```
Ensure the docker container is running and keep track of the container ID: 
- ```docker ps```
Now, through either an SSH tunnel or an alternative, navigate to ```http://localhost:3000``` and login to Grafana with the default authentication (username: admin, password: admin). Add Prometheus as a datasource (https://grafana.com/docs/grafana/v7.5/datasources/add-a-data-source/?utm_source=grafana_gettingstarted) by setting the URL to ```http://localhost:9090``` and the Access to ```Browser```. 
Finally, generate an API key by navigating to the API Keys tab within Grafana and generating a new API key with ```admin``` access and no expiration date. Save the API token value which starts with ```Bearer ...```. 

Also, at this time, you should add Prometheus as a data source. Navigate to the "Add a New Datasource" panel in the homepage of Grafana and select Prometheus from the list of options. For the URL field, input the Host OS IP and port in which you configured the Grafana container on. Select the 'Browser' option in the Access field. Finally, save the datasource. **Note:** Since Prometheus is not configured until later on in execution, this step may produce an error message from Grafana, but this should be fixed later on in the execution of these scripts. 

**Step 3: Fill out config file**
Within the ```PrometheusGrafana``` directory, fill out the requisite information mimicing a sample config file we have provided (e.g. ```topFlowConfig.yml```) to customize your dashboard for the flow you wish to visualize. Make sure to add the private Grafana API token to the config file at this step.

**Step 4: Configure the Node Exporter containers**
For each end system which you seek to visualize the node exporter metrics in, create a docker container in the host OS using the following command: 
- ```docker run -d \
     --net="host" \
     --pid="host" \
     -v "/:/host:ro,rslave" \
     quay.io/prometheus/node-exporter:latest \
     --path.rootfs=/host```
     
**Step 5: Configure the SNMP Exporter containers**
For each network element in the flow you wish to visualize, you must configure an SNMP Exporter on a host OS with access to the network element in the flow. For example, a flow with two end systems connected by a switch should be configured to have one (1) SNMP Exporter container on any one of the end systems. We provide scripts and supporting files within the ```SNMPExporter``` directory which will dynamically generate an SNMP Exporter container with a custom config file of the OIDs and scrape parameters specified by the user in the ```snmpConfig.yml``` file. Start by filling out the ```snmpConfig.yml``` file with your network topology details. Then, you may generate a custom SNMP exporter container (assuming you have docker pre-installed) with the following script command: 
- ```python3 dynamic.py snmpConfig.yml```

## Execution

Assuming the Dynamic Dashboard scripts have been configured, the Grafana docker container is running, the Node Exporter containers are running, and the SNMP Exporter container scripts have run, you can visualize your flow through Prometheus and Grafana with scripts from within the ```PrometheusGrafana``` directory. To run the script, issue the following command:
- ```python dynamic.py <config_file>```
where ```<config_file>``` is the user-generated config file detailing the configuration parameters of the flow we wish to visualize. Examples of sample config file formats are located within the ```PrometheusGrafana``` directory. 
