#! /bin/bash
MYIP=$(hostname -I | head -n1 | awk '{print $1;}')

read -r -p "Is ${MYIP} your IP address [y/N]: " correct_ip
if [ "$correct_ip" == "N" ] || [ "$correct_ip" == "n" ]; then
    read -r -p "Type in your ip address: " MYIP
fi

read -r -p "Enter number of host: " num_switch 
if [ "$num_switch" == "1" ] ; then
    read -r -p "Type in your switch ip address: " siwtchIP1
else 
    if [ "$num_switch" == "2" ] ; then
        read -r -p "Type in your switch 1 ip address: " siwtchIP1
        read -r -p "Type in your switch 2 ip address: " siwtchIP2
    fi
fi 

read -r -p "Enter host 1 ip address: " host1 
read -r -p "Enter host 2 ip address: " host2 

sed -i -e "s@198.32.43.16@${host1}@" .se_config/argsDef.sh
sed -i -e "s@198.32.43.16@${host1}@" .se_config/args.sh
sed -i -e "s@198.32.43.16@${host1}@" .se_config/multiDef.sh

# config the input host ip in argsDef 

# change localhost to ip address of the host

echo "||    Inserting ${MYIP} to prometheus.yml file"
echo "||    If the IP address is incorrect please update manually"
sed -i -e "s@your_ip:9091 @${MYIP}:9091 @" ../PrometheusGrafana/prometheus.yml

sleep 1
echo " "
echo "!!    MANUAL CONFIGURATION STEP"
echo "!!    Make sure you have configured config.yml before ./cloud/start.sh"
sleep 0.5
echo "!!    configuration templates are provided inside PrometheusGrafana/template"
echo "!!    Visit Google Doc for Grafana API Key instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub"
sleep 0.5
echo "!!    After Configuration: run ./start.sh to start Grafana-Prometheus-Pushgateway"
echo " "
sleep 0.5
read -p "Press enter to continue"
echo " "
