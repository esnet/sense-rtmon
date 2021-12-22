#!/usr/bin/env python3
import subprocess
import sys

if len(sys.argv) <= 1:
    # Stop and remove all docker containers
    subprocess.run("sudo docker stop $(docker ps -aq)", shell=True)
    subprocess.run("sudo docker rm $(docker ps -aq)", shell=True)
# Flag to save Grafana container
elif str(sys.argv[1]) == "--g" or str(sys.argv[1]) == "--G" or str(sys.argv[1]) == "--grafana":
    # Stop and remove all docker containers except for the Grafana container
    subprocess.run("sudo docker stop $(docker ps -a -q | grep -v 'grafana')", shell=True)
    subprocess.run("sudo docker rm $(docker ps -a -q | grep -v 'grafana')", shell=True)
# Remove SNMP Exporter generator and its dependencies
subprocess.run("sudo yum -y remove gcc gcc-c++ make net-snmp net-snmp-utils net-snmp-libs net-snmp-devel", shell=True)
subprocess.run("rm go1.13.linux-amd64.tar.gz.*", shell=True)
