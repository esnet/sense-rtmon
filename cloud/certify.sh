#! /bin/bash
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

docker run --rm -it -v /etc/letsencrypt:/etc/letsencrypt -p 80:80 certbot/certbot certonly \
             --standalone -n --agree-tos \
            --register-unsafely-without-email \
            --domains $domain