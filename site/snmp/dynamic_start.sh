#! /bin/bash

############################# PYTHON SCRIPT FILL OUT ####################
MYIP=1.1.1.1
pushgateway_server=dev2.virnao.com:9091
switch_target=10.10.10.10
############################# PYTHON SCRIPT FILL OUT ####################

############################# CRONTAB ###################################
echo "Starting Crontab setup"
# create a temporary copy paste file
> cron_autopush

echo "#Puppet Name: snmp exporter send data to pushgateway every 15 seconds" >> cron_autopush
echo "MAILTO=""" >> cron_autopush
echo "* * * * * for i in 0 1 2; do ${PWD}/crontabs/push_snmp_exporter_metrics.sh & sleep 15; done; ${PWD}/crontabs/push_snmp_exporter_metrics.sh" >> cron_autopush
crontab cron_autopush
echo "!!    crontab set up successfully"

############################# Crontab Task Files #############################
echo "Starting SNMP Exporter Service"
touch snmp_temp.txt
touch push_snmp_exporter_metrics.sh
chmod 755 push_snmp_exporter_metrics.sh
sudo tee push_snmp_exporter_metrics.sh<<EOF
#! /bin/bash
if curl ${MYIP}:9116/metrics | grep ".*"; then
    curl -o ${general_path}/site/crontabs/snmp_temp.txt ${MYIP}:9116/snmp?target=${switch_target}&module=if_mib
else
    > ${general_path}/site/crontabs/snmp_temp.txt	
fi
cat ${general_path}/site/crontabs/snmp_temp.txt | curl --data-binary @- ${pushgateway_server}/metrics/job/snmp-exporter/target_switch/${switch_target}/instance/${MYIP}
EOF

############################# Start SNMP #############################

cd snmp_exporter
echo "!!    Move generator.yml file to SNMP Exporter generator folder"
yes | cp -rfa /home/generator.yml /home/src/github.com/prometheus/snmp_exporter/generator/
make build
./src/github.com/prometheus/snmp_exporter/generator/generator generate
echo "snmp.yml generated"
./snmp_exporter