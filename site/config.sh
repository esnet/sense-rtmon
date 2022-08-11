#! /bin/bash
MYIP=$(hostname -I | head -n1 | awk '{print $1;}')

read -r -p "Is ${MYIP} your IP address [y/N]: " correct_ip
if [ "$correct_ip" == "N" ] || [ "$correct_ip" == "n" ]; then
    read -r -p "Type in your ip address: " MYIP
fi

# change args and config files
read -r -p "Enter host 1 ip address: " host1 
read -r -p "Enter host 2 ip address: " host2 
read -r -p "Enter number of host: " num_switch 
read -r -p "Enter DNS server name for https, enter ip address for http: " server_ip

sed -i -e "s@.*grafanaHostIP: .*@grafanaHostIP: '${server_ip}'@" ../config/config.yml

sed -i -e "s@.*hostIP: .*@hostIP: ${MYIP}@" ../config/config.yml
