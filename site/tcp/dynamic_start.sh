#! /bin/bash

############################# CRONTAB ###################################
echo "Starting Crontab setup"
> cron_autopush
echo "#Puppet Name: tcp exporter send data to pushgateway every 15 seconds" >> cron_autopush
echo "MAILTO=""" >> cron_autopush
echo "* * * * * for i in 0 1 2; do /home/update_tcp_exporter.sh & sleep 15; done; /home/update_tcp_exporter.sh" >> cron_autopush
crontab cron_autopush
echo "!!    crontab set up successfully"
############################# CRONTAB ###################################

############################# tcp #############################
touch update_tcp_exporter.sh
tee update_tcp_exporter.sh<<EOF
#! /bin/bash

EOF
echo "Starting TCP Exporter Service"

chmod 755 update_tcp_exporter.sh
# execute once before starting tcp exporter
./update_tcp_exporter.sh

crond
