#! /bin/bash
# START
echo "|| Grafana-Prometheus-Pushgateway Installer ||"
echo "||                                          ||"

## Read inputs
while getopts l: flag; do
    case "${flag}" in
    l) 
    # Prevents from unintended value for the flag.
        if [ $OPTARG -gt 3 ]; then
            echo "Flag ${OPTARG} not available"
            echo "The Flags Available: "
            echo "      1) Let's Encrypt signed certificate. (this machine must be reachable via over the internet by the domain name)"
            echo "      2) Using existing certificates."
            echo "      3) Finish install after downloading script exporter and setting up necessary dependencies"
            exit 1
        fi
        input_lets=${OPTARG} ;;
    # Push the error message to stderr
    *)  echo "Illegal option" >&2; 
        exit 1;;
        # stops the installation

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

# read -r -p "Please enter the IP Address of this host: " MYIP
echo "!!    Starting Docker Swarm"
docker swarm init
echo "!!    To learn more about Docker Swarm"
echo "!!    https://docs.docker.com/engine/reference/commandline/swarm_init/#--advertise-addr"

sleep 0.5

echo "!!    downloading script exporter"
git clone https://github.com/ricoberger/script_exporter.git

sleep 0.5

dnf update -y
yum update -y
sudo yum install -y docker-compose-plugin
sudo yum -y install firewalld
sudo yum –y install python3
sudo yum –y install python3-pip
sudo yum -y install lsof
sudo pip3 install pyyaml
sudo pip3 install requests
docker login
 
sleep 0.5

# >Certificates
echo "!!    Start Encryption Script"
sleep 0.5

if [ -z "$input_lets" ]; then
    echo "Let's Encrypt Certificate Setup for Grafana to enable https on port 3000: "
    echo "      1) Let's Encrypt signed certificate. (this machine must be reachable via over the internet by the domain name)"
    echo "      2) Using existing certificates."
    echo "      3) Finish Install."
    read -r -p "Select a mode [1]: " sslmode
    sslmode=${sslmode:-1}
else
    echo "Let's Encrypt command-line input found."
    # sslmode=${input_lets:-1}
    # ':-' Parameter Expansion is redundant because $input_lets will never be null in the else block.
    # Check is already done {-z "$input_lets"}
    sslmode=$input_lets
fi

if [ "$sslmode" == "1" ]; then # Let's Encrypt
    echo "    Note: port 80 must be available for DNS challenges to succeed. "
    echo "          See https://certbot.eff.org/faq for more information."
    read -r -p "Please enter the domain name of this machine: " domain
    echo "||             Certbot running for (${domain})..."
    if [ $(id -u) = 0 ]; then
        /bin/bash ./certify.sh ${domain}
    else
        echo "??            User is not root! Certbot requires root for security reasons."
        echo "              Please run the following script after installation: sudo /certify.sh ${domain}"
    fi
fi

if [ "$sslmode" == "2" ]; then # existing certificate
    echo "!!    Using existing certificates (e.g. default path /etc/pki/tls )."
    echo "Please enter the existing certificates and key:"
    read -r -p "ssl certificate (fullchain): " ssl_certificate
    if [[ -z "$ssl_certificate" ]]; then
        echo "Information incomplete: ssl certificate is missing."
        exit 1
    fi

    read -r -p "ssl certificate key (privkey): " ssl_certificate_key
    if [[ -z "$ssl_certificate_key" ]]; then
        echo "Information incomplete: ssl certificate key is missing."
        exit 1
    fi

    read -r -p "Please enter the domain name of this machine: " domain
    if [[ -z "$domain" ]]; then
        echo "Information incomplete: domain name is missing."
        exit 1
    fi

    read -r -p "Grafana Running port (default 3000 running behind Nginx): " grafana_port
    if [[ -z "$grafana_port" ]]; then
        grafana_port=3000
    fi
    read -r -p "Grafana Username: " grafana_user
    if [[ -z "$grafana_user" ]]; then
        echo "Information incomplete: needs username for config.yml."
        exit 1
    fi
    read -r -p "Grafana Password: " grafana_pass
    if [[ -z "$grafana_pass" ]]; then
        echo "Information incomplete: needs password for config.yml."
        exit 1
    fi
    read -r -p "Pushgateway Running port (default 9091 running behind Nginx): " pushgateway_port
    if [[ -z "$pushgateway_port" ]]; then
        pushgateway_port=9091
    fi
    read -r -p "Please enter sense-o-auth.yml path: " sense_path
    if [[ -z "$sense_path" ]]; then
        echo "Information incomplete: sense-o-auth.yml path is missing."
        exit 1
    fi

    cat > ../config_cloud/config.yml << EOF
ssl_certificate: "$ssl_certificate"
ssl_certificate_key: "$ssl_certificate_key"
domain: "$domain"
grafana_host: "http://grafana:$grafana_port"
grafana_public_domain: "http://$domain:$grafana_port"
pushgateway: "http://pushgateway:$pushgateway_port"
grafana_username: "$grafana_user"
grafana_password: "$grafana_pass"
grafana_api_token: ""
siterm_url_map:
  "urn:ogf:network:nrp-nautilus-prod.io:2020": https://sense-fe.nrp-nautilus.io:8443/T2_US_UCSD/sitefe//sitefe/json/frontend
  "urn:ogf:network:nrp-nautilus.io:2020": https://sense-prpdev-fe.sdn-lb.ultralight.org/T2_US_SDSC/sitefe/json/frontend
  "urn:ogf:network:ultralight.org:2013": https://sense-caltech-fe.sdn-lb.ultralight.org/T2_US_Caltech_Test/sitefe/json/frontend
  "urn:ogf:network:sc-test.cenic.net:2020": https://sense-ladowntown-fe.sdn-lb.ultralight.org/NRM_CENIC/sitefe/json/frontend
EOF

cat > ./docker-stack.yml << EOF

version: '3'

networks:
  monitor-net:

services:
  prometheus:
    image: prom/prometheus:v2.2.1
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - monitor-net
    logging:
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      placement:
        constraints:
          - node.role==manager

  pushgateway:
    image: prom/pushgateway
    ports:
      - 9091:9091
    deploy:
      placement:
        constraints:
          - node.role==manager
    logging:
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - monitor-net
  
  script_exporter:
    command:
      - '-config.file=/examples/config.yaml'
      - '-web.listen-address=:9469'
    image: 'ricoberger/script_exporter:v2.16.0'
    ports:
      - '9469:9469'
    volumes:
      - './script_exporter/examples:/examples'
    deploy:
      placement:
        constraints:
          - node.role==manager
      restart_policy:
        condition: on-failure
    networks:
      - monitor-net

  grafana:
    image: grafana/grafana-enterprise:10.4.2
    ports:
      - 3000:3000
    environment:
      GF_INSTALL_PLUGINS: jdbranham-diagram-panel
    networks:
      - monitor-net

  nginx:
    hostname: nginx
    image: nginx:1.21.6
    ports:
      - 443:443
      - 3000
    volumes:
      - $PWD/nginx/:/etc/nginx/conf.d/ # do not change this line if possible
      - $ssl_certificate:/etc/certificate/cert.pem
      - $ssl_certificate_key:/etc/certificate/privkey.pem
    networks:
      - monitor-net
  
  mainloop:
    image: mainloop:latest
    logging: 
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      placement:
        constraints:
          - node.role==manager
    volumes:
      - $sense_path:/root/.sense-o-auth.yaml
      - $ssl_certificate:/etc/certificate/cert.pem
      - $ssl_certificate_key:/etc/certificate/privkey.pem
    networks:
      - monitor-net
    
  # nginx reverse proxy Grafana to https


EOF
    cp ../config_cloud/config.yml .
    cp -r ../config_flow .
    docker build --network host -t mainloop .
    rm -r config_flow
    python3 certify.py ${domain} ${grafana_port} ${ssl_certificate} ${ssl_certificate_key}
    echo "!!    Success!"
    echo "!!    current ssl certificate updated in cloud/nginx/proxy_conf and cloud/nginx/server_conf"
    echo "!!    grafana port updated in docker-stack.yml file (default 3000)"
    echo "!!    make sure the same port is entered in config files in config_cloud/"
fi

echo "!!    what's next?"
echo "!!    run ./start.sh to start containers"
