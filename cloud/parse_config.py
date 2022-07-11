import os
import yaml
import json
import requests
import sys
import time
from subprocess import Popen, PIPE
import subprocess
        
config_data ={}
owd = os.getcwd()
os.chdir("..")
infpth = str(os.path.abspath(os.curdir)) + "/config.yml"
os.chdir(owd)

print("Loading Configuration File")
with open(infpth, 'r') as stream:
    try:
        config_data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("Config file load error!")

print("Parsing Config File")        
receiver_ip_address = "http://" + str(config_data['grafanaHostIP'])

pushgateway_ip = str(config_data['hostIP'])
switch_num = str(config_data['switchNum'])
host1 = str(config_data['HostA']['IP'])
host2 = str(config_data['HostB']['IP'])

if switch_num == "1":
    switch_ip = str(config_data['switchData']['SNMPHostIP'])
elif switch_num == "2":
    switch_ip = str(config_data['switchDataA']['SNMPHostIP'])
    switch_ip = str(config_data['switchDataB']['SNMPHostIP'])
