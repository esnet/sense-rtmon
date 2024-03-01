#!/bin/bash

# Copy files to current directory
cp "/etc/letsencrypt/live/dev2.virnao.com/privkey.pem" .
cp "/etc/letsencrypt/live/dev2.virnao.com/cert.pem" .
cp /root/.sense-o-auth.yaml .
cp ../config_cloud/config.yml .
cp -r ../config_flow .

# Build the Docker container with network host and interactive mode
docker build --network host -t mainloop .

# Run the Docker container in interactive mode
docker run -itd mainloop

# Remove the copied files
rm privkey.pem cert.pem .sense-o-auth.yaml config.yml
rm -r config_flow
