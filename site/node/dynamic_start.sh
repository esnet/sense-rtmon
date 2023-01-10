#! /bin/bash

############################# CRONTAB ###################################
echo "Starting Crontab setup"
> cron_autopush
echo "#Puppet Name: node exporter send data to pushgateway every 15 seconds" >> cron_autopush
echo "MAILTO=""" >> cron_autopush
echo "* * * * * for i in 0 1 2; do /home/push_node_exporter_metrics.sh & sleep 15; done; /home/push_node_exporter_metrics.sh" >> cron_autopush
crontab cron_autopush
echo "!!    crontab set up successfully"

############################# NODE #############################
echo "Starting Node Exporter Service"
tee push_node_exporter_metrics.sh<<EOF
#! /bin/bash
curl -s localhost:${NODE_PORT}/metrics | curl --data-binary @- ${PUSHGATEWAY_SERVER}/metrics/job/node-exporter/instance/${MYIP}
EOF
chmod 755 push_node_exporter_metrics.sh
crond

# run the node exporter from github
cd node_exporter
make build
./node_exporter --web.listen-address=:${NODE_PORT}