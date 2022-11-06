#! /bin/bash

echo "!!    Install go and pull node_exporter from Github"

wget https://dl.google.com/go/go1.18.3.linux-amd64.tar.gz
export PATH=${PATH}:/usr/local/go/bin
tar -C /usr/local -xzf go1.18.3.linux-amd64.tar.gz
rm -rf go1.18.3.linux-amd64.tar.gz
go env -w GO111MODULE=auto
go version
git clone https://github.com/prometheus/node_exporter.git

echo "!!    Start node exporter"