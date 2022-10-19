#! /bin/bash
cd ..
general_path=${PWD}
cd ./site

############################# DOCKER SETUP ##############################
## check docker 
read -r -p "Login to Docker [y/n]: " docker_login
if [ "${docker_login}" == "y" ] || [ "${docker_login}" == "Y" ]; then
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
    fi
fi
# sudo yum install -y docker-compose-plugin

############################## DOCKER SWARM ##############################

### !!! currently SWARM NOT USED 
echo "!!    Docker Swarm is not tested yet (recommend not using docker swarm)"
sleep 1
read -r -p "Init Docker Swarm [y/n]: " push_docker
if [ "${push_docker}" == "y" ] || [ "${push_docker}" == "Y" ]; then
    read -r -p "Please enter the IP Address of this host: " MYIP
    echo "!!    To learn more about Docker Swarm"
    echo "!!    https://docs.docker.com/engine/reference/commandline/swarm_init/#--advertise-addr"
    echo "!!    Initialize Docker Swarm"
    echo "${MYIP} is used for docker swarm advertise (IP is needed when there's more than one IP address on this host)"
    docker swarm init --advertise-addr ${MYIP}
else 
    echo "Skip Docker Swarm"
fi 

############################## INSTALL GO & SNMP DEPENDENCIES ##############################
read -r -p "Install SNMP Exporter [y/n]: " snmp_install
    if [ "${snmp_install}" == "y" ] || [ "${snmp_install}" == "Y" ]; then
    echo "!!    Install SNMP dependencies"
    echo "!!    Download go1.18.3"
    wget https://dl.google.com/go/go1.18.3.linux-amd64.tar.gz
    rm -rf /usr/local/go && tar -C /usr/local -xzf go1.18.3.linux-amd64.tar.gz # old go deleted
    export PATH=${PATH}:/usr/local/go/bin
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
    python3 install_snmp.py
    cd ..
fi

echo "!!    What's next?"
echo "!!    Install completed run ./start.sh to start exporters"