#! /bin/bash
########################### PLEASE DON'T CHANGE THIS FILE #######################
host1=
host2=
num_switch=
switchIP1=
switchIP2=

########################### Lines above are auto filled in ######################
read -r -p "Enter your ip address: " MYIP 

# change args and config files
# read -r -p "Enter host 1 ip address: " host1 
# read -r -p "Enter host 2 ip address: " host2 
# read -r -p "Enter number of swtich: " num_switch 

# sed -i -e "s@.*pushgateway=1.*@pushgateway=${MYIP}@" .se_config/argsDef.sh
# sed -i -e "s@.*instance=1.*@instance=${host1}@" .se_config/argsDef.sh
# sed -i -e "s@.*ip_address=1.*@ip_address=${host2}@" .se_config/argsDef.sh
# sed -i -e "s@.*netElNum=.*@netElNum=${num_switch}@" .se_config/argsDef.sh 

# # echo "optional "
# if [ "$num_switch" == "1" ] ; then
#     # read -r -p "Type in your switch ip address: " switchIP1
# else 
#     if [ "$num_switch" == "2" ] ; then
#         # read -r -p "Type in your switch 1 ip address: " switchIP1
#         # read -r -p "Type in your switch 2 ip address: " switchIP2
#         sed -i -e "s@.*netElIP2=1.*@netElIP2=${switchIP2}@" .se_config/argsDef.sh 
#     fi
# fi

# if [ "$num_switch" != "0" ] ; then
#     sed -i -e "s@.*netElIP=1.*@netElIP=${switchIP1}@" .se_config/argsDef.sh 
# fiz 

echo "||    Inserting ${MYIP} to prometheus.yml file"
echo "||    If the IP address is incorrect please update manually"
sed -i -e "s@your_ip:9091 @${MYIP}:9091 @" ./dashboard/prometheus.yml

# sleep 0.5
# echo "!!    configuration templates are provided inside dashboard/template"
# echo "!!    Visit Google Doc for Grafana API and add Promethues as a Data Source Key instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub"
# sleep 0.5
# echo "!!    After Configuration: run ./start.sh to start Grafana-Prometheus-Pushgateway"
# echo " "
# sleep 0.5
# read -p "Press enter to continue"
# echo " "
