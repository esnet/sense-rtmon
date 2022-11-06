#! /bin/bash

############################# PYTHON SCRIPT FILL OUT ####################
MYIP=
pushgateway_server=

############################# CRONTAB ###################################
echo "Starting Crontab setup"
touch cron_autopush
echo "#Puppet Name: node exporter send data to pushgateway every 15 seconds" >> cron_autopush
echo "MAILTO=""" >> cron_autopush
echo "* * * * * for i in 0 1 2; do ${PWD}/push_node_exporter_metrics.sh & sleep 15; done; ${PWD}/push_node_exporter_metrics.sh" >> cron_autopush
crontab cron_autopush
echo "!!    crontab set up successfully"

############################# NODE #############################
echo "Starting Node Exporter Service"
sudo tee push_node_exporter_metrics.sh<<EOF
#! /bin/bash
curl -s ${MYIP}:9100/metrics | curl --data-binary @- ${pushgateway_server}/metrics/job/node-exporter/instance/${MYIP}
EOF
chmod 755 push_node_exporter_metrics.sh

# run the node exporter from github
cd node_exporter
make build
./node_exporter &