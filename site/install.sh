#! /bin/bash

# install dependencies
yum install -y p7zip p7zip-plugins make
current_pwd=$PWD
# check docker 
if [ -x "$(command -v docker)" ]; then
    echo "||        Found docker..."
    echo "||        Running docker login..."
    docker login
else
    echo "!!    Docker command not found."
    echo "!!    Please visit https://docs.docker.com/install/ for installation instructions."
    exit 1
fi

# check docker compose
if [ -x "$(command -v docker compose)" ]; then
    echo "||        Found docker compose..."
    echo "||        Running docker login..."
    docker login
else
    echo "!!    Docker compose command not found."
    echo "!!    Installing docker compose"
    suod yum install -y docker-compose-plugin
    docker login
    # exit 1
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

read -r -p "Set up bash script? [y/N (Enter)]: " bashstart
if [ "$bashstart" == "y" ] || [ "$bashstart" == "Y" ]; then
    echo "creating bash scripts"
    echo "!!    Setting up bash files to autopush Node and SNMP metrics to Pushgateway"
    if [ -f "/root/push_node_exporter_metrics.sh" ]; then
        echo "push_node_exporter_metrics.sh already exits"
        chmod +x /root/push_node_exporter_metrics.sh
    else
        touch /root/push_node_exporter_metrics.sh
        chmod +x /root/push_node_exporter_metrics.sh
        sudo tee /root/push_node_exporter_metrics.sh<<EOF
curl -s ${MYIP}:9100/metrics | curl --data-binary @- $pushgateway_server/metrics/job/node-exporter/instance/$MYIP
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
curl -s ${MYIP}:9116/metrics | curl --data-binary @- $pushgateway_server/metrics/job/snmp-exporter/instance/$MYIP
EOF
fi

    echo ""
    if [ -f "../Metrics/update_arp_exporter.sh" ]; then
        echo "update_arp_exporter.sh already exits"
        chmod +x /Metrics/update_arp_exporter.sh
        mkdir ../Metrics/ARPMetrics/jsonFiles
        mkdir ../Metrics/ARPMetrics/arpFiles
        touch ../Metrics/ARPMetrics/arpFiles/arpOut-.txt
        touch ../Metrics/ARPMetrics/jsonFiles/arpOut-.json
    else
        mkdir ../Metrics/ARPMetrics/jsonFiles
        mkdir ../Metrics/ARPMetrics/arpFiles
        touch ../Metrics/ARPMetrics/arpFiles/arpOut-.txt
        touch ../Metrics/ARPMetrics/jsonFiles/arpOut-.json
        touch /Metrics/update_arp_exporter.sh
        chmod +x /Metrics/update_arp_exporter.sh
        sudo tee /Metrics/update_arp_exporter.sh<<EOF
arp -a > $current_pwd/../Metrics/ARPMetrics/arpFiles/arpOut-.txt
python3 $current_pwd/../Metrics/ARPMetrics/convertARP.py $current_pwd/../Metrics/ARPMetrics/arpFiles/arpOut-.txt $current_pwd/../Metrics/ARPMetrics/jsonFiles/arpOut-.json
EOF
fi
else 
    echo "Nothing installed"
fi

read -r -p "Set up crontab? [y/N (Enter)]: " crontab
if [ "$crontab" == "y" ] || [ "$crontab" == "Y" ]; then
    echo "Satring Crontab setup"
    # create a temporary copy paste file
    echo ""
    if [ -f "/root/cron_autopush" ]; then
        echo "cron_autopush already exits"
    else
        touch /root/cron_autopush
        touch /root/cron_history
    fi

    echo "!!    copy paste crontab to a temporary file"
    crontab -l > /root/cron_autopush
    crontab -l > /root/cron_history

    # check if job is alread in
    if grep -F "/root/push_snmp_exporter_metrics.sh" /root/cron_autopush 
    then
        echo "task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: snmp exporter data to pushgateway every 15 seconds" >> /root/cron_autopush
        echo "MAILTO=""" >> /root/cron_autopush
        echo "* * * * * for i in 0 1 2; do /root/push_snmp_exporter_metrics.sh & sleep 15; done; /root/push_snmp_exporter_metrics.sh" >> /root/cron_autopush
    fi

    if grep -F "/root/push_node_exporter_metrics.sh" /root/cron_autopush
    then    
        echo "task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: node exporter data to pushgateway every 15 seconds" >> /root/cron_autopush
        echo "MAILTO=""" >> /root/cron_autopush
        echo "* * * * * for i in 0 1 2; do /root/push_node_exporter_metrics.sh & sleep 15; done; /root/push_node_exporter_metrics.sh" >> /root/cron_autopush
    fi

    if grep -F "/root/update_arp_exporter.sh" /root/cron_autopush
    then    
        echo "task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: check update on arp table every 15 seconds" >> /root/cron_autopush
        echo "MAILTO=""" >> /root/cron_autopush
        echo "* * * * * for i in 0 1 2; do $current_pwd/../Metrics/ARPMetrics/update_arp_exporter.sh & sleep 15; done; $current_pwd/../Metrics/ARPMetrics/update_arp_exporter.sh" >> /root/cron_autopush
    fi

    echo ""
    crontab /root/cron_autopush
    rm -f /root/cron_autopush
    echo "!!    crontab set up successfuly"
else 
    echo "Skip crontab, crontab is needed to push metrics successfully"
fi
