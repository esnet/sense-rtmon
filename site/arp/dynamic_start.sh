#! /bin/bash

############################# PYTHON SCRIPT FILL OUT ####################
host2IP=
############################# PYTHON SCRIPT FILL OUT ####################

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
touch arp_out.txt
touch arp_out.json
touch delete.json
touch prev.json
touch ping_status.txt
touch prev_ping_status.txt

touch update_arp_exporter.sh
chmod 755 update_arp_exporter.sh
sudo tee update_arp_exporter.sh<<EOF
#! /bin/bash
/sbin/arp -a > /home/arp_out.txt
# sleep 0.5
python3 /home/convert_arp.py /home/arp_out.txt /home/arp_out.json
# sleep 0.5
ping -c 1 ${host2IP}
if [ $? -eq 0 ]; then 
  echo "${host2IP}/ping_status/1" > /home/ping_status.txt
else
  echo "${host2IP}/ping_status/0" > /home/ping_status.txt
fi
EOF
echo "Starting ARP Exporter Service"
