#! /bin/bash

if [ -x "$(command -v docker)" ]; then
    echo "||        Found docker..."
    echo "||        Running docker login..."
    docker login
    echo "||        Checking docker swarm..."
    docker swarm init # &>/dev/null
else
    echo "!!    Docker command not found."
    echo "!!        Please visit https://docs.docker.com/install/ for installation instructions."
    exit 1
fi

# get correct IP address
MYIP=$(hostname -I | head -n1 | awk '{print $1;}')
read -r -p "Is ${MYIP} your IP address [y/N]: " correct_ip
if [ "$correct_ip" == "N" ] || [ "$correct_ip" == "n" ]; then
    read -r -p "Type in your ip address: " MYIP
fi

# get pushgateway server
read -r -p "Enter Pushgateway server IP address (e.g. http://dev2.virnao.com:9091): " pushgateway_server

echo "!!    Initialize Docker Swarm"
echo "$MYIP is used for docker swarm advertise"
docker swarm init --advertise-addr $MYIP

echo "!!    Setting up Crontab to autopush Node and SNMP metrics to Pushgateway"
if [ -f "/root/push_node_exporter_metrics.sh" ]; then
    echo "push_node_exporter_metrics.sh already exits"
    chmod +x /root/push_node_exporter_metrics.sh
else
    touch /root/push_node_exporter_metrics.sh
    chmod +x /root/push_node_exporter_metrics.sh
    sudo tee /root/push_node_exporter_metrics.sh<<EOF
curl -s localhost:9100/metrics | curl --data-binary @- $pushgateway_server/metrics/job/node-exporter/instance/$MYIP
EOF
fi

echo ""
if [ -f "/root/push_snmp_exporter_metrics.sh" ]; then
    echo "push_snmp_exporter_metrics.sh already exits"
    chmod +x /root/push_snmp_exporter_metrics.sh
else
    touch /root/push_snmp_exporter_metrics.sh
    chmod +x /root/push_snmp_exporter_metrics.sh
    sudo tee /root/push_snmp_exporter_metrics.sh<<EOF
curl -s localhost:9116/metrics | curl --data-binary @- $pushgateway_server/metrics/job/snmp-exporter/instance/$MYIP
EOF
fi

# create a temporary copy paste file
echo ""
if [ -f "/root/cron_autopush" ]; then
    echo "cron_autopush already exits"
else
    touch /root/cron_autopush
fi

echo "!!    copy paste crontab to a temporary file"
crontab -l > /root/cron_autopush

# check if port already in the crontab
if grep -F "/root/push_snmp_exporter_metrics.sh" /root/cron_autopush 
then
    echo "task is already in cron, type crontab -e to check"
else
    echo "#Puppet Name: snmp exporter data to pushgateway every 15 seconds" >> /root/cron_autopush
    echo "MAILTO=""" >> /root/cron_autopush
    echo "* * * * * for i in 0 1 2; do /root/push_snmp_exporter_metrics.sh & sleep 15; done; /root/push_snmp_exporter_metrics.sh" >> /root/cron_autopush
fi
     grep -F "/root/push_node_exporter_metrics.sh" /root/cron_autopush
    echo "task is already in cron, type crontab -e to check"
else
    echo "#Puppet Name: node exporter data to pushgateway every 15 seconds" >> /root/cron_autopush
    echo "MAILTO=""" >> /root/cron_autopush
    echo "* * * * * for i in 0 1 2; do /root/push_node_exporter_metrics.sh & sleep 15; done; /root/push_node_exporter_metrics.sh" >> /root/cron_autopush
fi

crontab /root/cron_autopush
rm -f /root/cron_autopush
echo "!!    crontab set up complete"
