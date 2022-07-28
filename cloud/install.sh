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
sleep 0.5

echo "!!    downloading script exporter"
git clone https://github.com/ricoberger/script_exporter.git
yes | cp -rfa se_config/. script_exporter/examples

sleep 0.5

# install grafana
sudo tee  /etc/yum.repos.d/grafana.repo<<EOF
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

sleep 0.5

sudo yum -y install grafana
sudo yum -y install firewalld
sudo yum –y install python3
sudo yum –y install python3-pip
sudo pip3 install pyyaml
sudo pip3 install requests

sleep 0.5

# echo "!!    IMPORTANT"
# echo "!!    Enable port 3000"
# sleep 0.5
# sudo systemctl enable --now grafana-server
# sudo systemctl enable firewalld
# sudo firewall-cmd --add-port=3000/tcp --permanent
# sudo firewall-cmd --reload
sudo systemctl start grafana-server
echo "!!    Grafana is running on http://localhost:3000"
echo "!!    Start Configuration Script"

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


# sudo tee /etc/yum.repos.d/nginx.repo<<EOF
# [nginx]
# name=nginx repo
# baseurl=https://nginx.org/packages/centos/$releasever/$basearch/
# gpgcheck=0
# enabled=1
# EOF
sudo dnf install nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# server {
#     listen 80;
#     server_name dev2.virnao.com;
#     return 301 https://dev2.virnao.com$request_uri;
# }

# server {
#     server_name dev2.virnao.com;
#     listen 443 ssl http2;
#     listen [::]:443 ssl http2;
#     ssl on;
#     ssl_certificate /etc/nginx/ssl-certs/godaddy_cert.crt;
#     ssl_certificate_key /etc/nginx/ssl-certs/godaddy_key.key;
#     root /var/www/dev2.virnao.com;
#     index index.html;
#     location / {
#         proxy_pass http://localhost:3000/;
#         proxy_set_header Host $http_host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto “https”;
#     }
# }