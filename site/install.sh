#! /bin/bash
cd ..
general_path=$PWD
cd ./site

# read -r -p "Enter the IP adress of this host for docker swarm to init --advertise-addr <IP> " MYIP

############################## DOCKER SETUP ##############################
### check docker 
# read -r -p "Login to Docker [y/N (press enter is default N)]: " docker_login
# if [ "$docker_login" == "y" ] || [ "$docker_login" == "Y" ]; then
#     if [ -x "$(command -v docker)" ]; then
#         echo "||        Found docker..."
#         echo "||        Running docker login..."
#         docker login
#     else
#         echo "!!    Docker command not found."
#         echo "!!    Please visit https://docs.docker.com/install/ for installation instructions."
#         exit 1
#     fi

#     # check docker compose
#     if [ -x "$(command -v docker compose)" ]; then
#         echo "||        Found docker compose..."
#         echo "||        Running docker login..."
#         docker login
#     else
#         echo "!!    Docker compose command not found."
#         echo "!!    Installing docker compose"
#         # suod yum install -y docker-compose-plugin
#         docker login
#         # exit 1
#     fi
# fi
sudo yum install -y docker-compose-plugin

############################## DOCKER SWARM ##############################

### !!! currently SWARM NOT USED 
# read -r -p "Init Docker Swarm [y/N (press enter is default N)]: " push_docker
# if [ "$push_docker" == "y" ] || [ "$push_docker" == "Y" ]; then
#     # read -r -p "Enter Pushgateway server IP address (e.g. http://dev2.virnao.com:9091): " pushgateway_server
#     echo "!!    Initialize Docker Swarm"
#     echo "$MYIP is used for docker swarm advertise"

#     read -r -p "Init Docker Swarm [y/N (press enter is default N)]: " swarm_init
#     if [ "$swarm_init" == "y" ] || [ "$swarm_init" == "Y" ]; then
#         docker swarm init --advertise-addr $MYIP
#     fi
# else 
#     echo "Skip Docker Swarm"
# fi 

############################## INSTALL GO & SNMP DEPENDENCIES ##############################
read -r -p "Install SNMP Exporter [y/N (press enter is default N)]: " snmp_install
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
    # Make mibs, and install SNMP exporter. Config could be done later
    
    sleep 0.2
    echo "!!    Go build and Make mibs.."
    cd ./SNMPExporter
    python3 ./SNMPExporter/install_snmp.py
    cd ..

    # read -r -p "Enter MIB folder (default /usr/share/snmp/mibs): " mibfolder
    # echo "!!    Download MIBS"
    # echo "!!    MIBFOLDER: $mibfolder"
    # export MIBDIRS=$mibfolder
    # echo "!!    to change mib folder run: export MIBDIRS=<>"
    # wget -O $mibfolder/FORCE10-SMI https://www.circitor.fr/Mibs/Mib/F/FORCE10-SMI.mib
    # wget -O $mibfolder/F10-IF-EXTENSION-MIB https://www.circitor.fr/Mibs/Mib/F/F10-IF-EXTENSION-MIB.mib
    # wget -O $mibfolder/F10-FIB-MIB http://www.circitor.fr/Mibs/Mib/F/F10-FIB-MIB.mib
    # wget -O $mibfolder/F10-FPSTATS-MIB https://www.circitor.fr/Mibs/Mib/F/F10-FPSTATS-MIB.mib
    # echo "!!    To download addtional mibs follow this instruction: "
    # echo "!!    wget -O /usr/share/snmp/mibs/<MIBS_name> https://www.circitor.fr/Mibs/Mib/<First_letter_of_MIBS_name>/<MIBS_name>.mib"
    # echo "!!    Example: wget -O /usr/share/snmp/mibs/F10-IF-EXTENSION-MIB https://www.circitor.fr/Mibs/Mib/F/F10-IF-EXTENSION-MIB.mib"
fi

############################## AUTOPUSH CRONTAB SETUP ##############################

# read -r -p "Set up crontab? [y/N (press enter is default N)]: " crontab
# if [ "$crontab" == "y" ] || [ "$crontab" == "Y" ]; then
#     echo "Satring Crontab setup"
#     # create a temporary copy paste file
#     echo ""
#     > ./crontabs/cron_autopush
#     > ./crontabs/cron_history

#     echo "!!    copy paste crontab to a temporary file"
#     crontab -l > ./crontabs/cron_autopush
#     crontab -l > ./crontabs/cron_history

#     # check if job is alread in
#     if grep -F "push_snmp_exporter_metrics.sh" ./crontabs/cron_autopush 
#     then
#         echo "task is already in cron, type crontab -e to check"
#     else
#         echo "#Puppet Name: snmp exporter send data to pushgateway every 15 seconds" >> ./crontabs/cron_autopush
#         echo "MAILTO=""" >> ./crontabs/cron_autopush
#         echo "* * * * * for i in 0 1 2; do $PWD/crontabs/push_snmp_exporter_metrics.sh & sleep 15; done; $PWD/crontabs/push_snmp_exporter_metrics.sh" >> ./crontabs/cron_autopush
#     fi

#     if grep -F "push_node_exporter_metrics.sh" ./crontabs/cron_autopush
#     then    
#         echo "task is already in cron, type crontab -e to check"
#     else
#         echo "#Puppet Name: node exporter send data to pushgateway every 15 seconds" >> ./crontabs/cron_autopush
#         echo "MAILTO=""" >> ./crontabs/cron_autopush
#         echo "* * * * * for i in 0 1 2; do $PWD/crontabs/push_node_exporter_metrics.sh & sleep 15; done; $PWD/crontabs/push_node_exporter_metrics.sh" >> ./crontabs/cron_autopush
#     fi

#     if grep -F "update_arp_exporter.sh" ./crontabs/cron_autopush
#     then    
#         echo "task is already in cron, type crontab -e to check"
#     else
#         echo "#Puppet Name: check update on arp table every 15 seconds" >> ./crontabs/cron_autopush
#         echo "MAILTO=""" >> ./crontabs/cron_autopush
#         echo "* * * * * for i in 0 1 2; do $PWD/crontabs/update_arp_exporter.sh & sleep 15; done; $PWD/crontabs/update_arp_exporter.sh" >> ./crontabs/cron_autopush
#     fi

#     echo ""
#     crontab ./crontabs/cron_autopush
#     rm -f ./crontabs/cron_autopush
#     echo "!!    crontab set up successfuly"
# else 
#     echo "Skip crontab, crontab is needed to push metrics successfully"
# fi

echo "install completed run ./start.sh to start exporters"