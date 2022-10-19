#! /bin/bash

docker run --rm -it -v /etc/letsencrypt:/etc/letsencrypt -p 80:80 certbot/certbot certonly \
--standalone -n --agree-tos \
--register-unsafely-without-email \
--domains $1

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

    read -r -p "Grafana Running port (default 3000): " grafana_port
    python3 certify.py $1 ${grafana_port}  "/opt/sense-rtmon/tls/tls.crt" "/opt/sense-rtmon/tls/tls.key"
else
    echo "!!    Certificate not found! Error during TLS configuration."
    exit 1
fi