#! /bin/bash
cd ..
general_path=$PWD
cd ./site

############################## DOCKER SETUP ##############################

# check docker 
read -r -p "Login to Docker [y/N enter]: " docker_login
if [ "$docker_login" == "y" ] || [ "$docker_login" == "Y" ]; then
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
fi
############################## DOCKER SWARM and PUSHGATEWAY ##############################

# get correct IP address
MYIP=$(hostname -I | head -n1 | awk '{print $1;}')
read -r -p "Is ${MYIP} your IP address [y/N]: " correct_ip
if [ "$correct_ip" == "N" ] || [ "$correct_ip" == "n" ]; then
    read -r -p "Type in your ip address: " MYIP
fi
read -r -p "Enter VLAN (e.g. 1000): " VLAN

# get host2 IP address
read -r -p "Enter host2 IP address (if needed): " host2IP

# get pushgateway server
read -r -p "Build connection to pushgateway and init Docker Swarm [y/N (Enter)]: " push_docker
if [ "$push_docker" == "y" ] || [ "$push_docker" == "Y" ]; then
    read -r -p "Enter Pushgateway server IP address (e.g. http://dev2.virnao.com:9091): " pushgateway_server
    echo "!!    Initialize Docker Swarm"
    echo "$MYIP is used for docker swarm advertise"

    read -r -p "Init Docker Swarm [y/N (Enter)]: " swarm_init
    if [ "$swarm_init" == "y" ] || [ "$swarm_init" == "Y" ]; then
        docker swarm init --advertise-addr $MYIP
    fi
else 
    echo "Skip pushgateway and docker swarm"
fi 

############################## INSTALL GO & SNMP DEPENDENCIES ##############################
read -r -p "Install SNMP Exporter [y/N (Enter)]: " snmp_install
    if [ "$snmp_install" == "y" ] || [ "$snmp_install" == "Y" ]; then
    echo "!!    Install SNMP dependencies"
    echo "!!    Download go1.18.3"
    wget https://dl.google.com/go/go1.18.3.linux-amd64.tar.gz
    rm -rf /usr/local/go && tar -C /usr/local -xzf go1.18.3.linux-amd64.tar.gz # old go deleted
    export PATH=$PATH:/usr/local/go/bin
    go env -w GO111MODULE=auto
    go version
    rm -rf go1.18.3.linux-amd64.tar.gz
    sleep 0.2
    
    dnf update -y
    yum update -y 

    dnf install kernel-devel make gcc gcc-c++ -y --disableexcludes=all
    yum install -y p7zip p7zip-plugins make gcc gcc-c++ net-snmp net-snmp-utils net-snmp-libs net-snmp-devel
    yum install gcc gcc-c+
    # Make mibs, and install SNMP exporter. Config could be done late
    
    sleep 0.2
    echo "!!    Go build and Make mibs.."
    cd ..
    cd ./SNMPExporter
    python3 dynamic.py
    cd ..
    cd ./site
fi

############################## AUTOPUSH BASH SCRIPTS SETUP ##############################

read -r -p "Set up bash script? [y/N (Enter)]: " bashstart
if [ "$bashstart" == "y" ] || [ "$bashstart" == "Y" ]; then
    echo "creating bash scripts"
    echo "!!    Setting up bash files to autopush Node and SNMP metrics to Pushgateway"
    > ./crontabs/push_node_exporter_metrics.sh
    chmod +x ./crontabs/push_node_exporter_metrics.sh
    sudo tee ./crontabs/push_node_exporter_metrics.sh<<EOF
#! /bin/bash
curl -s ${MYIP}:9100/metrics | curl --data-binary @- $pushgateway_server/metrics/job/node-exporter/instance/$MYIP
EOF

    # if [ -f "/root/push_snmp_exporter_metrics.sh" ]; then

    read -r -p "Enter switch IP :" switchIP
    touch ./crontabs/push_snmp_exporter_metrics_$VLAN.sh
    chmod +x ./crontabs/push_snmp_exporter_metrics_$VLAN.sh
    sudo tee ./crontabs/push_snmp_exporter_metrics_$VLAN.sh<<EOF
#! /bin/bash
if curl 198.32.43.16:9116/metrics | grep ".*"; then
    curl -o snmp_temp.txt ${MYIP}:9116/snmp?target=$switchIP&module=if_mib
else
    > snmp_temp.txt	
fi
cat snmp_temp.txt | curl --data-binary @- $pushgateway_server/metrics/job/snmp-exporter/vlan/$VLAN/instance/$MYIP
EOF

    echo ""
    mkdir ../Metrics/ARPMetrics/jsonFiles
    mkdir ../Metrics/ARPMetrics/arpFiles
    touch ../Metrics/ARPMetrics/arpFiles/arpOut.txt
    touch ../Metrics/ARPMetrics/jsonFiles/arpOut.json
    touch ../Metrics/ARPMetrics/jsonFiles/delete.json
    touch ../Metrics/ARPMetrics/jsonFiles/prev.json
    touch ../Metrics/ARPMetrics/pingStat/ping_status.txt
    touch ./crontabs/update_arp_exporter.sh
    chmod +x ./crontabs/update_arp_exporter.sh

else 
    echo "Nothing installed"
fi

############################## AUTOPUSH CRONTAB SETUP ##############################

read -r -p "Set up crontab? [y/N (Enter)]: " crontab
if [ "$crontab" == "y" ] || [ "$crontab" == "Y" ]; then
    echo "Satring Crontab setup"
    # create a temporary copy paste file
    echo ""
    > ./crontabs/cron_autopush
    > ./crontabs/cron_history

    echo "!!    copy paste crontab to a temporary file"
    crontab -l > ./crontabs/cron_autopush
    crontab -l > ./crontabs/cron_history

    # check if job is alread in
    if grep -F "push_snmp_exporter_metrics_$VLAN.sh" ./crontabs/cron_autopush 
    then
        echo "task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: snmp exporter vlan $VLAN send data to pushgateway every 15 seconds" >> ./crontabs/cron_autopush
        echo "MAILTO=""" >> ./crontabs/cron_autopush
        echo "* * * * * for i in 0 1 2; do $PWD/crontabs/push_snmp_exporter_metrics_$VLAN.sh & sleep 15; done; $PWD/crontabs/push_snmp_exporter_metrics_$VLAN.sh" >> ./crontabs/cron_autopush
    fi

    if grep -F "push_node_exporter_metrics.sh" ./crontabs/cron_autopush
    then    
        echo "task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: node exporter send data to pushgateway every 15 seconds" >> ./crontabs/cron_autopush
        echo "MAILTO=""" >> ./crontabs/cron_autopush
        echo "* * * * * for i in 0 1 2; do $PWD/crontabs/push_node_exporter_metrics.sh & sleep 15; done; $PWD/crontabs/push_node_exporter_metrics.sh" >> ./crontabs/cron_autopush
    fi

    if grep -F "update_arp_exporter.sh" ./crontabs/cron_autopush
    then    
        echo "task is already in cron, type crontab -e to check"
    else
        echo "#Puppet Name: check update on arp table every 15 seconds" >> ./crontabs/cron_autopush
        echo "MAILTO=""" >> ./crontabs/cron_autopush
        echo "* * * * * for i in 0 1 2; do $PWD/crontabs/update_arp_exporter.sh & sleep 15; done; $PWD/crontabs/update_arp_exporter.sh" >> ./crontabs/cron_autopush
        # * * * * * /root/awsvm/DynamicDashboard/Metrics/ARPMetrics/update_arp_exporter.sh
        # every minute instead of 15 seconds
    fi

    echo ""
    crontab ./crontabs/cron_autopush
    rm -f ./crontabs/cron_autopush
    echo "!!    crontab set up successfuly"
else 
    echo "Skip crontab, crontab is needed to push metrics successfully"
fi
