#!/usr/bin/env python3
import subprocess
import sys
import os

# Defaults to save the running Grafana container if it exists
if len(sys.argv) <= 1:
    # Stop and remove all docker containers except for the Grafana container
    subprocess.run("sudo docker stop $(docker ps -aq)", shell=True)
    subprocess.run("sudo docker start grafana", shell=True)
    # subprocess.run("sudo docker rm $(docker ps -aq)", shell=True)
# Flag to remove the running Grafana container
elif str(sys.argv[1]) == "--a" or str(sys.argv[1]) == "--A" or str(sys.argv[1]) == "--all":
    # Stop and remove all docker containers
    subprocess.run("sudo docker stop $(docker ps -aq)", shell=True)
    # subprocess.run("sudo docker rm $(docker ps -aq)", shell=True)
# Remove SNMP Exporter generator and its dependencies
# subprocess.run("sudo docker rm $(docker ps -aq)", shell=True)
subprocess.run("sudo yum -y remove gcc gcc-c++ make net-snmp net-snmp-utils net-snmp-libs net-snmp-devel", shell=True)
subprocess.run("rm -R tcpFiles", shell=True)
subprocess.run("rm -R jsonFiles", shell=True)
dir = str(os.getcwd())
goLoc = dir + "/SNMPExporter"
subprocess.run("rm go1.13.linux-amd64.tar.gz", shell=True, cwd = goLoc)
subprocess.run("rm go1.13.linux-amd64.tar.gz.*", shell=True, cwd = goLoc)
