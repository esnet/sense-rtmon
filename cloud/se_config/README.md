## config.yml
- configures the script exporter
- The last line sets the bash script to run:
- scripts:
  - name: default
    script: ./examples/l2debugging.sh

## generate_script.py
- reads a given config file under `config_flow`
- generates a bash script dynamically

## l2debugging.sh
- curl the pushgateway site
- find the correlation between each host and switch

## File path
- after generation, `l2debugging.sh` and `config.yml` are moved to `script_exporter/example/folder`
- script exporter is then restarted to run the new script