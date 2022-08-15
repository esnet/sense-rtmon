#! /bin/bash
# START
echo "|| Grafana-Prometheus-Pushgateway Installer ||"
echo "||                                          ||"

## Read inputs
while getopts l: flag; do
    case "${flag}" in
    l) input_lets=${OPTARG} ;;
    esac
done

if [ -x "$(command -v docker)" ]; then
    echo "||        Found docker..."
    echo "||        Running docker login..."
    docker login
else
    echo "!!    Docker command not found."
    echo "!!        Please visit https://docs.docker.com/install/ for installation instructions."
    exit 1
fi

sleep 0.5

echo "!!    downloading script exporter"
git clone https://github.com/ricoberger/script_exporter.git
yes | cp -rfa se_config/. script_exporter/examples

sleep 0.5

dnf update -y
yum update -y
suod yum install -y docker-compose-plugin
sudo yum -y install firewalld
sudo yum –y install python3
sudo yum –y install python3-pip
sudo pip3 install pyyaml
sudo pip3 install requests
docker login
 
sleep 0.5

# Configuration starts
/bin/bash ./config.sh

# >Certificates
echo "!!    Start Encryption Script"
sleep 0.5

if [ -z "$input_lets" ]; then
    echo "Let's Encrypt Certificate Setup for Grafana to enable https on port 3000: "
    echo "      1) Let's Encrypt signed certificate. (this machine must be reachable via over the internet by the domain name)"
    echo "      2) Finish Install."
    read -r -p "Select a mode [1]: " sslmode
    sslmode=${sslmode:-1}
else
    echo "Let's Encrypt command-line input found."
    sslmode=${input_lets:-1}
fi
if [ "$sslmode" == "1" ]; then # Let's Encrypt
    echo "    Note: port 80 must be available for DNS challenges to succeed. "
    echo "          See https://certbot.eff.org/faq for more information."
    read -r -p "Please enter the domain name of this machine: " domain
    echo "||             Certbot running for ($domain)..."
    if [ $(id -u) = 0 ]; then
        /bin/bash ./certify.sh $domain
    else
        echo "??            User is not root! Certbot requires root for security reasons."
        echo "              Please run the following script after installation: sudo /certify.sh $domain" 
    fi
fi
