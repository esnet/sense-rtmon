#! /bin/bash

############################# PYTHON SCRIPT FILL OUT ####################
MYIP=1.1.1.1
pushgateway_server=dev2.virnao.com:9091
switch_target=10.10.10.10
private_mib=placeholder
############################# PYTHON SCRIPT FILL OUT ####################

############################# CRONTAB ###################################
echo "Starting Crontab setup"
# create a temporary copy paste file
> cron_autopush

echo "#Puppet Name: snmp exporter send data to pushgateway every 15 seconds" >> cron_autopush
echo "MAILTO=""" >> cron_autopush
echo "* * * * * for i in 0 1 2; do /home/push_snmp_exporter_metrics.sh & sleep 15; done; /home/push_snmp_exporter_metrics.sh" >> cron_autopush
crontab cron_autopush
echo "!!    crontab set up successfully"

############################# Crontab Task Files #############################
echo "Starting SNMP Exporter Service"
touch snmp_temp.txt
touch push_snmp_exporter_metrics.sh
chmod 755 push_snmp_exporter_metrics.sh
tee push_snmp_exporter_metrics.sh<<EOF
#! /bin/bash
if curl localhost:9116/metrics | grep ".*"; then
    curl -o /home/snmp_temp.txt localhost:9116/snmp?target=${SWITCH_TARGET}&module=if_mib
else
    > /home/snmp_temp.txt	
fi
cat /home/snmp_temp.txt | curl --data-binary @- ${PUSHGATEWAY_SERVER}/metrics/job/snmp-exporter/target_switch/${SWITCH_TARGET}/instance/${MYIP}
EOF

############################# Start SNMP #############################
echo "!!    Correct MIBS environment variable"

echo "!!    Move generator.yml file to SNMP Exporter generator folder"
yes | cp -rfa /home/generator.yml /home/snmp_exporter/generator/
echo "!!    Set correct mibs folder"
# Avoid including all elements, it will take a long time with warnings to generate SNMP.yml file later
# make it include in the config file in the future
export MIBDIRS=/home/librenms/mibs/
# export MIBDIRS=${MIBDIRS}:/home/librenms/mibs/cisco/
# export MIBDIRS=${MIBDIRS}:/home/librenms/mibs/dell/
export MIBDIRS=${MIBDIRS}:/home/librenms/mibs/${PRIVATE_MIB}

echo "!!    Generating snmp.yml file"
cd /home/snmp_exporter/generator
go build
./generator generate
echo "!!    snmp.yml file generated"

echo "!!    Move generated snmp.yml file to binary release folder where snmp_exporter is ran"
yes | cp -rfa /home/snmp_exporter/generator/snmp.yml /home/snmp_exporter-0.21.0.linux-amd64/

cd /home/snmp_exporter-0.21.0.linux-amd64/
./snmp_exporter