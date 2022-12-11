#! /bin/bash

############################# CRONTAB ###################################
echo "Starting Crontab setup"
> cron_autopush
echo "#Puppet Name: arp exporter send data to pushgateway every 15 seconds" >> cron_autopush
echo "MAILTO=""" >> cron_autopush
echo "* * * * * for i in 0 1 2; do /home/update_arp_exporter & sleep 15; done; /home/update_arp_exporter" >> cron_autopush
crontab cron_autopush
echo "!!    crontab set up successfully"
############################# CRONTAB ###################################

############################# ARP #############################
touch /home/arp_out.txt
touch /home/arp_out.json
touch /home/delete.json
touch /home/prev.json
touch /home/ping_status.txt
touch /home/prev_ping_status.txt

touch update_arp_exporter.sh
sudo tee update_arp_exporter.sh<<EOF
#! /bin/bash
/sbin/arp -a > /home/arp_out.txt
# sleep 0.5
python3 /home/convert_arp.py /home/arp_out.txt /home/arp_out.json
# sleep 0.5
ping -c 1 ${HOST2IP}
if [ $? -eq 0 ]; then 
  echo "${HOST2IP}/ping_status/1" > /home/ping_status.txt
else
  echo "${HOST2IP}/ping_status/0" > /home/ping_status.txt
fi
EOF
echo "Starting ARP Exporter Service"

chmod 755 update_arp_exporter.sh
crond
