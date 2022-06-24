#! /bin/bash
MYIP=$(hostname -I | head -n1 | awk '{print $1;}')

read -r -p "Is ${MYIP} your IP address [y/N]: " correct_ip

if [ "$correct_ip" == "N" ] || [ "$correct_ip" == "n" ]; then
    read -r -p "Type in your ip address: " MYIP
fi

echo "||    Inserting ${MYIP} to prometheus.yml file"
echo "||    If the IP address is incorrect please update manually"
sed -i -e "s@your_ip:9091 @${MYIP}:9091 @" /root/DynamicDashboard/PrometheusGrafana/prometheus.yml

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
