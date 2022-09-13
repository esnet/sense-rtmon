# Site Configuration files under `config_cloud`
The configuration files are broken into 3 sections.
- General Information is needed for all exporters.
- SNMP Metrics is only needed if SNMP exporter is running on this host. It can be ommitted if SNMP not used.  
- TCP and ARP are needed to indicate which ports are used when TCP and ARP exporters are running. **Currently the `scrapeDuration` and `scrapeInterval` do not function.**

## Section 1 General Information
- `switchNum` is the number of switches that the host is connected to and are intended to be monitored.
- `hostIP` is the IP address of the host. If Docker Stack is used, make sure it's the same IP when initializing Docker Stack.
- `pushgatewayPort` the port where pushgateway is running on on `Could Stack`. Do not change this number unless the cloud stack has changed its port mapping in `cloud/docker-stack.yml`.
- `grafanaHostIP` the DNS of the server that `Cloud Stack` runs on. If DNS not available use IP address but it'll not be encrypted.
- `hostA` and `hostB`'s IP addresses are needed.

## Section 2 SNMP Metrics
- `SNMPHostIP` the IP address of this host if the SNMP exporter is running on it.
- `target` the IP address of the switch where the metrics are pulling from.
- `portIn` and `portOut` contain the interface name and interface vlan used for filtering SNMP metrics before sending it to `Cloud Stack`. **Currently, it's not implemented yet.**
- `oids` enter the name or number of oids to pull from the switch.
- `communityString` the key needed to access the swtich. Please keep the quotation marks.
- `scrapeTimeout` and `retries` by default is 5s and 3.
**Note: Scale Up SNMP Metrics when there is more than one switch**
- If there is more than 1 switch copy paste the enter SNMP section and name each switch `snmpMetricsA`, `snmpMetricsB`, `snmpMetricsC` ... `multiconfig.yml` is a good example.


## Section 3 TCP and ARP
- `port` used for dashboard to display the information.
- `job_name` used for dashboard naming each exporter.
- This section might add more exporters in the future. 