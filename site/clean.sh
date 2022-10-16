#! /bin/bash
echo "!!    Removing related Stack, Containers, Compose"
systemctl stop node_exporter
docker stack rm site
docker compose down -v

docker rm -f compose-files-snmp-exporter-1 compose-files-tcp-exporter-1 compose-files-arp-exporter-1 compose-files-node-exporter-1  compose-files-snmp-exporter2-1 compose-files-snmp-exporter3-1 compose-files-snmp-exporter4-1 compose-files-snmp-exporter5-1 compose-files-snmp-exporter6-1 compose-files-snmp-exporter7-1 compose-files-snmp-exporter8-1 compose-files-snmp-exporter9-1 compose-files-snmp-exporter10-1

# it deletes 10 SNMP exporters, just in case 10 exist

docker image rm -f arp_exporter:latest tcp_exporter:latest

rm -rf ./crontabs/push_snmp_exporter_metrics*.sh ./crontabs/snmp_* ./crontabs/temp_push_snmp_exporter_metrics.sh
rm -rf ./crontabs/push_node_exporter_metrics*.sh  
rm -rf ./crontabs/update_arp_exporter*

rm -rf ./compose-files/added*

read -r -p "Erase Metrics [y/n]: " erase
if [ "$erase" == "y" ] || [ "$erase" == "Y" ]; then
    echo "!!    Erase pushgateway urls sent from this host"
    read -r -p "Enter the config file used to start: (press enter to choose default config file /config_site/config.yml or type the config file WITHOUT path): " erase_config
    python3 erase_pushgateway.py $erase_config
    echo "!!    Cleaning Complete"
else 
    echo "Nothing on Pushgateway is Erased"
fi

read -r -p "Remove all SNMP related downloads and config files [y/n]?: " remove_SNMP
if [ "$remove_SNMP" == "y" ] || [ "$remove_SNMP" == "Y" ]; then
    cd SNMPExporter
    rm -rf go* pkg src bin snmp*.yml
    echo "Files, under SNMPExporter, generated from ./install.sh are deleted"
else
    echo "SNMPExporter files can be found under SNMPExporter"
fi