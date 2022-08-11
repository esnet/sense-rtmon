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

sed -i -e "s@.*grafanaHostIP: .*@grafanaHostIP: =${server_ip}@" ../config/config.yml

sed -i -e "s@.*pushgateway=1.*@pushgateway=${MYIP}@" .se_config/argsDef.sh
sed -i -e "s@.*instance=1.*@instance=${host1}@" .se_config/argsDef.sh
sed -i -e "s@.*ip_address=1.*@ip_address=${host2}@" .se_config/argsDef.sh
sed -i -e "s@.*netElNum=.*@netElNum=${num_switch}@" .se_config/argsDef.sh 

# echo "optional "
if [ "$num_switch" == "1" ] ; then
    read -r -p "Type in your switch ip address: " switchIP1
else 
    if [ "$num_switch" == "2" ] ; then
        read -r -p "Type in your switch 1 ip address: " switchIP1
        read -r -p "Type in your switch 2 ip address: " switchIP2
        sed -i -e "s@.*netElIP2=1.*@netElIP2=${switchIP2}@" .se_config/argsDef.sh 
    fi
fi

if [ "$num_switch" != "0" ] ; then
    sed -i -e "s@.*netElIP=1.*@netElIP=${switchIP1}@" .se_config/argsDef.sh 
fi 

echo "||    Inserting ${MYIP} to prometheus.yml file"
echo "||    If the IP address is incorrect please update manually"
sed -i -e "s@your_ip:9091 @${MYIP}:9091 @" ./dashboard/prometheus.yml

sleep 1
echo " "
echo "!!    MANUAL CONFIGURATION STEP"
echo "!!    Make sure you have configured config.yml before ./cloud/start.sh"
sleep 0.5
echo "!!    configuration templates are provided inside dashboard/template"
echo "!!    Visit Google Doc for Grafana API Key instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub"
sleep 0.5
echo "!!    After Configuration: run ./start.sh to start Grafana-Prometheus-Pushgateway"
echo " "
sleep 0.5
read -p "Press enter to continue"
echo " "
