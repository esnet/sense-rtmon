#! /bin/bash

docker run --rm -it -v /etc/letsencrypt:/etc/letsencrypt -p 80:80 certbot/certbot certonly \
-n --agree-tos \
--register-unsafely-without-email \
--domains $1
# --standalone 
if [ -f "/opt/certbot/live/$1/fullchain.pem" ]; then
    echo "!!    Copying certificates from /opt/certbot/live/$1/ to /opt/sense-rtmon/tls/"
    mkdir -p /opt/sense-rtmon/tls/
    # /etc/pki/tls
    cd /opt/sense-rtmon/tls/

    cp /opt/certbot/live/$1/fullchain.pem tls.crt
    cp /opt/certbot/live/$1/privkey.pem tls.key
    chmod 0777 tls.crt
    chmod 0777 tls.key
    # # Building keystore.
    # openssl pkcs12 -export -in tls.crt -inkey tls.key \
    #     -certfile tls.crt -out keystore.p12 -password pass:$tls_pass
    
    # # Converting keystore.
    # rm -f server.keystore    
    # keytool -importkeystore \
    #     -srckeystore keystore.p12 -srcstoretype pkcs12 -srcstorepass $tls_pass \
    #     -destkeystore server.keystore -deststoretype JKS -deststorepass $tls_pass
    # rm -f keystore.p12

    # # Configuring keystore.
    # keytool -changealias -alias 1 -destalias server -keystore server.keystore -storepass $tls_pass
    # chmod 0777 server.keystore

        sudo tee ./nginx/server_conf<<EOF
server_name $1;
ssl_certificate     "/opt/sense-rtmon/tls/tls.crt";
ssl_certificate_key "/opt/sense-rtmon/tls/tls.key";
EOF

first_line="proxy_pass http://$1:3000/;"
sed -i.bak "1s/.*/$first_line/" ./nginx/proxy_conf

else
    echo "!!    Certificate not found! Error during TLS configuration."
    exit 1
fi

# usage() {
#     cat <<EOF
#         Usage:      letsencrypt.sh <domain> 
#         Arguments:
#                     - domain: domain name of the server
# EOF
# }

# if [ $# = 1 ]; then
#     domain=$1
#     # if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
#     #     echo "!!    Already Certified"
#     #     exit 1
#     # fi
#     # install tools
#     sudo yum install snapd
#     sudo systemctl enable --now snapd.socket
#     sudo ln -s /var/lib/snapd/snap /snap
#     sudo snap install core
#     sudo snap refresh core
#     # installation and certification
#     sudo snap install --classic certbot

#     if [ $(id -u) = 0 ]; then
#         sudo ln -s /snap/bin/certbot /usr/bin/certbot
#         sudo certbot certonly --standalone -n --agree-tos \
#             --register-unsafely-without-email \
#             --domains $domain
#         if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
#             cp /etc/letsencrypt/live/$domain/*.pem /etc/grafana/
#             # chown :grafana /etc/grafana/fullchain.pem
#             # chown :grafana /etc/grafana/privkey.pem
#             chown :grafana /etc/letsencrypt/live/$domain/fullchain.pem
#             chown :grafana /etc/letsencrypt/live/$domain/etc/grafana/privkey.pem
#             chmod 640 /etc/letsencrypt/live/$domain/fullchain.pem
#             chmod 640 /etc/letsencrypt/live/$domain/etc/grafana/privkey.pem

#             # edit grafana initialization file
#             # echo "!!    Manual Configuration might be needed"
#             # echo "!!    Replacing string in /etc/grafana/grafana.ini"
#             # echo "!!    ;protocol =http->protocol = https@"
#             # echo "!!    ;cert_file =->cert_file = /etc/grafana/fullchain.pem@"
#             # echo "!!    ;cert_key =->cert_key = /etc/grafana/privkey.pem@"

#             # sed -i -e 's@;protocol = http@protocol = https@' /etc/grafana/grafana.ini
#             # # sed -i '/;protocol = http/a\protocol = https' /etc/grafana/grafana.ini
#             # sed -i -e 's@;cert_file =@cert_file = /etc/grafana/fullchain.pem@' /etc/grafana/grafana.ini
#             # sed -i 's@;cert_key =@cert_key = /etc/grafana/privkey.pem@' /etc/grafana/grafana.ini

#             # # restart
#             # grafana-cli plugins install jdbranham-diagram-panel
#             # sudo service grafana-server restart
#         else
#             echo "!!    Certificate not found!"
#             exit 1
#         fi
#     else
#         echo "!!    User is not root. Please run script with sudo."
#     fi
# else 
#     echo "!!    Invalid arguments passed."
#     usage
# fi