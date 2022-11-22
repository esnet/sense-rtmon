#! /bin/bash
cd ..
general_path=${PWD}
cd ./site


############################# PYTHON SCRIPT FILL OUT ####################
MYIP=1.1.1.1
host2IP=2.2.2.2
switch_target1=10.10.10.10
switch_target2=11.11.11.11
switchNum=2
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


############################# NODE #############################
read -r -p "Start Node Exporter? [y/n]: " start_node
if [ "${start_node}" == "y" ] || [ "${start_node}" == "Y" ]; then
    starting_node="-f ./compose-files/node-docker-compose.yml" 
    start_exporters="${start_exporters} ${starting_node}"
    echo "Starting Node Exporter Service"
    sudo tee ./crontabs/push_node_exporter_metrics.sh<<EOF
#! /bin/bash
curl -s ${MYIP}:9100/metrics | curl --data-binary @- ${pushgateway_server}/metrics/job/node-exporter/instance/${MYIP}
EOF
    chmod 755 ./crontabs/push_node_exporter_metrics.sh
else
    starting_node=" " 
    echo "Skip Node Exporter"
fi

############################# SNMP #############################
echo "Starting SNMP Exporter Service"
touch ./crontabs/snmp_temp.txt
touch ./crontabs/push_snmp_exporter_metrics.sh
chmod 755 ./crontabs/push_snmp_exporter_metrics.sh
sudo tee ./crontabs/push_snmp_exporter_metrics.sh<<EOF
#! /bin/bash
if curl ${MYIP}:9116/metrics | grep ".*"; then
    curl -o ${general_path}/site/crontabs/snmp_temp.txt ${MYIP}:9116/snmp?target=${switch_target1}&module=if_mib
else
    > ${general_path}/site/crontabs/snmp_temp.txt	
fi
cat ${general_path}/site/crontabs/snmp_temp.txt | curl --data-binary @- ${pushgateway_server}/metrics/job/snmp-exporter/target_switch/${switch_target1}/instance/${MYIP}
EOF