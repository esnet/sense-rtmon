# Cloud Configuration files under `config_flow`
The configuration files are broken into 3 sections.
- General Information is needed for all exporters.
- SNMP Metrics are only needed if the SNMP exporter is running on this host. It can be omitted if SNMP is not used. 
- TCP and ARP are needed to indicate which ports are used when TCP and ARP exporters are running. **Currently the `scrapeDuration` and `scrapeInterval` do not function.**

## Naming convention
- each config file should be named as `config-flow-SOME_GLOBAL_ID.yml`
- global ID is an unique number that can be traced and requested by the orchestrator.

## Section 1 General Information
- `switchNum` is the number of switches that the host is connected to and are intended to be monitored.
- `dashTitle` title was used for the first Grafana dashboard that includes Node and SNMP metrics.
- `debugTitle` title for debugging dashboard that includes ARP and SNMP metrics.
- `flow` is a unique identifier that represents a flow number.
- `hostIP` is the IP address of the host. If Docker Stack is used, make sure it's the same IP when initializing Docker Stack.
- `grafanaHostIP` is the DNS of the server that `Cloud Stack` runs on. If DNS is not available use an IP address but it'll not be encrypted.
- `grafanaPort` the port where Grafana is running on default is 3000. Do not change it unless the port mapping in `cloud/docker-stack.yml` is changed.
- `pushgatewayPort` is the port where pushgateway is running on `Could Stack`. Do not change this number unless the `Cloud Stack` has changed its port mapping in `cloud/docker-stack.yml`.
- `grafanaAPIToken` API token that establishes the initial connection. Auto Curl is supported in the `start.sh` script. This can be left blank. For manual
Instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub
- `configFile` indicates the config file used.

### Host Information
- `IP` addresses of hostA and hostB are needed.
- `interfaceName` is used in Grafana to query node metrics.
- `interfaceName`, `interfadeIP`, and `nodeName` are displayed on the dashboard and the diagram.
- `vlan` is included in the title of each dashboard.
- `ifName` and `ifVlan` are used to query SNMP metrics coming from `Site Stack`.
- `order` indicates the diagram connection of host devices from left to right.

## Section 2 SWITCH INFORMATION
- `SNMPHostIP` is the IP address of this host if the SNMP exporter is running on it.
- `target` the IP address of the switch where the metrics are pulling from.
- `portIn` and `portOut` contain the interface name and interface VLAN used for querying SNMP metrics. **NOTE: This requires SNMP Exporter to run before generating the dashboard**
- `order` indicates the diagram connection of switches from left to right.
- `switchif` is optional. It's displayed on the diagram.
**Note: Scale Up SNMP Metrics when there is more than one switch**
- If there is more than 1 switch copy and paste the enter SNMP section and name each switch `snmpMetricsA`, `snmpMetricsB`, `snmpMetricsC` ... `multiconfig.yml` is a good example.

## Section 3 TCP and ARP
- `port` is used for the dashboard to display the information.
- `job_name` is used for the dashboard naming each exporter.
- This section might add more exporters in the future. 