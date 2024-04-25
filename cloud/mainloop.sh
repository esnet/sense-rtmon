#!/bin/bash


IMAGE_NAME="mainloop:latest"


VOLUME_CERTS="/home/centos/certificates/.sense-o-auth.yaml:/root/.sense-o-auth.yaml"
VOLUME_SSL_CERT="/etc/letsencrypt/live/dev2.virnao.com/cert.pem:/etc/certificate/cert.pem"
VOLUME_SSL_KEY="/etc/letsencrypt/live/dev2.virnao.com/privkey.pem:/etc/certificate/privkey.pem"


NETWORK="monitor-net"


docker network ls | grep -w "$NETWORK" || docker network create "$NETWORK"


docker run -d \
  --name mainloop \
  --network $NETWORK \
  --mount type=bind,source=/home/centos/certificates/.sense-o-auth.yaml,target=/root/.sense-o-auth.yaml \
  --mount type=bind,source=/etc/letsencrypt/live/dev2.virnao.com/cert.pem,target=/etc/certificate/cert.pem \
  --mount type=bind,source=/etc/letsencrypt/live/dev2.virnao.com/privkey.pem,target=/etc/certificate/privkey.pem \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  $IMAGE_NAME


docker ps -f name=mainloop
