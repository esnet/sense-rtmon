# Cloud Configuration files under `config_flow`
The configuration files are broken into 2 sections.
- General Information is needed for dashboard generation.
- `hostname` and `sitename` are needed for sending requests to `siterm` API.


## Section 1 General Information
- `flow` is a unique identifier that represents a specific flow (the current design might change where siterm will filter out flows).
- `title` is the IP address of the host. If Docker Stack is used, make sure it's the same IP when initializing Docker Stack.
- `grafana_host` is the DNS of the server that `Cloud Stack` runs on. If DNS is not available use an IP address but it'll not be encrypted. `http://dev2.virnao.com:3000`
- `pushgateway` example: `http://dev2.virnao.com:9091`
- `grafana_api_token` API token that establishes the initial connection. Auto Curl is supported in the `generate.sh` and `generate_backend.sh` script. This can be left blank. For manual
Instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub

## Section 2 Nodes
Each node has a `name`, `type`, `runtime` indicates how long the exporters will run in seconds, `sense_mon_id` (not used experimenting),`interface`. Each `interface` has a `name`, `ip` and `vlan`. `vlan` and `ip` are optional. Each interface might have a `peer` or more.

### Host Node
- `type` is host
- `arp` indicates the siterm to turn on or off arp exporters
- `ip` is the ip address of the host. L2 debugging checks the arp table of each host to see if the `ip` could be found in the arp table 

### Switch Node
- `type` is switch
- `interface` contains all the connections that need to be monitored