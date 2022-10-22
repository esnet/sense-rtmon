import json
import os
import yaml
import sys
import re 
import subprocess
from datetime import datetime

# read in a yml file and returns a data dictionary and file name used
def read_yml_file(path, sys_argv, order, go_back_folder_num):
    # locate path
    if path[0] != "/":
        path = "/" + path
    owd = os.getcwd()
    for i in range(go_back_folder_num):
        os.chdir("..")
    config_path = str(os.path.abspath(os.curdir)) + path
    infpth = config_path + "/config.yml"
    os.chdir(owd)
    data = {}
    file_name = "config.yml"

    # argument given
    if len(sys_argv) > 1:
        file_name = str(sys_argv[order])
        file_path = config_path + "/" + file_name
        print(f"\n Config file {file_path}\n")
        with open(file_path, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(f"\n Config file {file_path} could not be found in the config directory\n")
        
    else: # default config file
        with open(infpth, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(f"\n Config file {infpth} could not be found in the config directory\n")
    
    return data,file_name

# replace variables with strings in a json file
def replacing_json(input,output,data,replacements):
    with open(input) as infile, open(output, 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                # target = str(target)
                line = line.replace(src, target)
            outfile.write(line)
            
# make a template of replacement that can be used for up to 10 switches
def replacement_template():
    replacements = {
    'IPHOSTA': "IPHOSTA", 
    'IPHOSTB': "IPHOSTB",
    'VLANA': "VLANA",
    'VLANB': "VLANB",
    
    'MONITORVLAN1': "MONITORVLAN1",
    'MONITORVLAN2': "MONITORVLAN2",
    'MONITORVLAN3': "MONITORVLAN3",
    'MONITORVLAN4': "MONITORVLAN4",
    'MONITORVLAN5': "MONITORVLAN5",
    'MONITORVLAN6': "MONITORVLAN6",
    'MONITORVLAN7': "MONITORVLAN7",
    'MONITORVLAN8': "MONITORVLAN8",
    'MONITORVLAN9': "MONITORVLAN9",
    'MONITORVLAN10': "MONITORVLAN10",
    'MONITORVLAN11': "MONITORVLAN11",
    'MONITORVLAN12': "MONITORVLAN12",
    'MONITORVLAN13': "MONITORVLAN13",
    'MONITORVLAN14': "MONITORVLAN14",
    'MONITORVLAN15': "MONITORVLAN15",
    'MONITORVLAN16': "MONITORVLAN16",
    'MONITORVLAN17': "MONITORVLAN17",
    'MONITORVLAN18': "MONITORVLAN18",
    'MONITORVLAN19': "MONITORVLAN19",
    'MONITORVLAN20': "MONITORVLAN20",
    
    'IFNAMEHOSTA': "IFNAMEHOSTA",
    'IFNAMEHOSTB': "IFNAMEHOSTB",
    'SNMP1HOSTIP': "SNMP1HOSTIP",
    'SNMP2HOSTIP': "SNMP2HOSTIP",
    'SNMP3HOSTIP': "SNMP3HOSTIP",
    'SNMP4HOSTIP': "SNMP4HOSTIP",
    'SNMP5HOSTIP': "SNMP5HOSTIP",
    'SNMP6HOSTIP': "SNMP6HOSTIP",
    'SNMP7HOSTIP': "SNMP7HOSTIP",
    'SNMP8HOSTIP': "SNMP8HOSTIP",
    'SNMP9HOSTIP': "SNMP9HOSTIP",
    'SNMP10HOSTIP': "SNMP10HOSTIP",
    
    'NAMEIFSWITCHA': "NAMEIFSWITCHA",
    'NAMEIFSWITCHB': "NAMEIFSWITCHB",
    'NAMEIFSWITCHC': "NAMEIFSWITCHC",
    'NAMEIFSWITCHD': "NAMEIFSWITCHD",
    'NAMEIFSWITCHE': "NAMEIFSWITCHE",
    'NAMEIFSWITCHF': "NAMEIFSWITCHF",
    'NAMEIFSWITCHG': "NAMEIFSWITCHG",
    'NAMEIFSWITCHH': "NAMEIFSWITCHH",
    'NAMEIFSWITCHI': "NAMEIFSWITCHI",
    'NAMEIFSWITCHJ': "NAMEIFSWITCHJ",
    
    'SWITCHIFA':"SWITCHIFA",
    'SWITCHIFB':"SWITCHIFB",
    'SWITCHIFC':"SWITCHIFC",
    'SWITCHIFD':"SWITCHIFD",
    'SWITCHIFE':"SWITCHIFE",
    'SWITCHIFF':"SWITCHIFF",
    'SWITCHIFG':"SWITCHIFG",
    'SWITCHIFH':"SWITCHIFH",
    'SWITCHIFI':"SWITCHIFI",
    'SWITCHIFJ':"SWITCHIFJ",
    
    'SWITCHAINVLAN':  "SWITCHAINVLAN",
    'SWITCHAOUTVLAN': "SWITCHAOUTVLAN",
    'SWITCHBINVLAN':  "SWITCHBINVLAN",
    'SWITCHBOUTVLAN': "SWITCHBOUTVLAN",
    'SWITCHCINVLAN':  "SWITCHCINVLAN",
    'SWITCHCOUTVLAN': "SWITCHCOUTVLAN",
    'SWITCHDINVLAN':  "SWITCHDINVLAN",
    'SWITCHDOUTVLAN': "SWITCHDOUTVLAN",
    'SWITCHEINVLAN':  "SWITCHEINVLAN",
    'SWITCHEOUTVLAN': "SWITCHEOUTVLAN",
    'SWITCHFINVLAN':  "SWITCHFINVLAN",
    'SWITCHFOUTVLAN': "SWITCHFOUTVLAN",
    'SWITCHGINVLAN':  "SWITCHGINVLAN",
    'SWITCHGOUTVLAN': "SWITCHGOUTVLAN",
    'SWITCHHINVLAN':  "SWITCHHINVLAN",
    'SWITCHHOUTVLAN': "SWITCHHOUTVLAN",
    'SWITCHIINVLAN':  "SWITCHIINVLAN",
    'SWITCHIOUTVLAN': "SWITCHIOUTVLAN",
    'SWITCHJINVLAN':  "SWITCHJINVLAN",
    'SWITCHJOUTVLAN': "SWITCHJOUTVLAN",
    
    'SWITCHAOUTGOING': "SWITCHAOUTGOING",
    'SWITCHAINCOMING': "SWITCHAINCOMING",
    'SWITCHBINCOMING': "SWITCHBINCOMING",
    'SWITCHBOUTGOING': "SWITCHBOUTGOING",
    'SWITCHCINCOMING': "SWITCHCINCOMING",
    'SWITCHCOUTGOING': "SWITCHCOUTGOING",
    'SWITCHDINCOMING': "SWITCHDINCOMING",
    'SWITCHDOUTGOING': "SWITCHDOUTGOING",
    'SWITCHEOUTGOING': "SWITCHEOUTGOING",
    'SWITCHEINCOMING': "SWITCHEINCOMING",
    'SWITCHFINCOMING': "SWITCHFINCOMING",
    'SWITCHFOUTGOING': "SWITCHFOUTGOING",
    'SWITCHGINCOMING': "SWITCHGINCOMING",
    'SWITCHGOUTGOING': "SWITCHGOUTGOING",
    'SWITCHHINCOMING': "SWITCHHINCOMING",
    'SWITCHHOUTGOING': "SWITCHHOUTGOING",
    'SWITCHIOUTGOING': "SWITCHIOUTGOING",
    'SWITCHIINCOMING': "SWITCHIINCOMING",
    'SWITCHJINCOMING': "SWITCHJINCOMING",
    'SWITCHJOUTGOING': "SWITCHJOUTGOING",
    
    'IFINDEXSWITCHHOSTA': "IFINDEXSWITCHHOSTA",
    'IFINDEXSWITCHHOSTB': "IFINDEXSWITCHHOSTB",
    
    'NAMEIFAIN':  "NAMEIFAIN",
    'NAMEIFAOUT': "NAMEIFAOUT",
    'NAMEIFBIN':  "NAMEIFBIN",
    'NAMEIFBOUT': "NAMEIFBOUT",
    'NAMEIFCIN':  "NAMEIFCIN",
    'NAMEIFCOUT': "NAMEIFCOUT",
    'NAMEIFDIN':  "NAMEIFDIN",
    'NAMEIFDOUT': "NAMEIFDOUT",
    
    'DATAPLANEIPA': "DATAPLANEIPA",
    'DATAPLANEIPB': "DATAPLANEIPB",
    'NODENAMEA': "NODENAMEA",
    'NODENAMEB': "NODENAMEB",
    
    'IPSWITCHA': "IPSWITCHA",
    'IPSWITCHB': "IPSWITCHB",
    'IPSWITCHC': "IPSWITCHC",
    'IPSWITCHD': "IPSWITCHD",
    
    'SNMPANAME': "SNMPANAME",
    'SNMPBNAME': "SNMPBNAME",
    'SNMPCNAME': "SNMPCNAME",
    'SNMPDNAME': "SNMPDNAME",
    'SNMPENAME': "SNMPENAME",
    'SNMPFNAME': "SNMPFNAME",
    'SNMPGNAME': "SNMPGNAME",
    'SNMPHNAME': "SNMPHNAME",
    'SNMPINAME': "SNMPINAME",
    'SNMPJNAME': "SNMPJNAME",

    'SWITCHAINVLAN':  "SWITCHAINVLAN",
    'SWITCHAOUTVLAN': "SWITCHAOUTVLAN",
    'SWITCHBINVLAN':  "SWITCHBINVLAN",
    'SWITCHBOUTVLAN': "SWITCHBOUTVLAN",
    'SWITCHCINVLAN':  "SWITCHCINVLAN",
    'SWITCHCOUTVLAN': "SWITCHCOUTVLAN",
    'SWITCHDINVLAN':  "SWITCHDINVLAN",
    'SWITCHDOUTVLAN': "SWITCHDOUTVLAN",
    'SWITCHEINVLAN':  "SWITCHEINVLAN",
    'SWITCHEOUTVLAN': "SWITCHEOUTVLAN",
    'SWITCHFINVLAN':  "SWITCHFINVLAN",
    'SWITCHFOUTVLAN': "SWITCHFOUTVLAN",
    'SWITCHGINVLAN':  "SWITCHGINVLAN",
    'SWITCHGOUTVLAN': "SWITCHGOUTVLAN",
    'SWITCHHINVLAN':  "SWITCHHINVLAN",
    'SWITCHHOUTVLAN': "SWITCHHOUTVLAN",
    'SWITCHIINVLAN':  "SWITCHIINVLAN",
    'SWITCHIOUTVLAN': "SWITCHIOUTVLAN",
    'SWITCHJINVLAN':  "SWITCHJINVLAN",
    'SWITCHJOUTVLAN': "SWITCHJOUTVLAN",
    
    'DASHTITLE': "DASHTITLE",
    'DEBUGTITLE': "DEBUGTITLE"}

    return replacements

# make a title according to the configuration file
def make_title(data):
    current_time = datetime.now().strftime("%m/%d_%H:%M")
    timeTxt = " | [" + str(current_time) + "]"        
    title = f" {str(data['flow'])} || {str(data['configFile'])} || {str(data['hostA']['interfaceName'])}/{str(data['hostA']['vlan'])}-- {data['switchNum']}-switch --{str(data['hostB']['interfaceName'])}/{str(data['hostB']['vlan'])} {timeTxt}"
    return title

def index_finder(name,pushgateway_metrics):
    cmd = f"curl {pushgateway_metrics} | tac | grep '.*ifName.*ifName=\"{name}\".*'"
    grep = subprocess.check_output(cmd,shell=True).decode()
    if_index = re.search('ifIndex="(.+?)\"',grep).group(1)
    return if_index

# def fill_replacement(data):
#     dash_title = data["dashTitle"] + make_title(data)
#     debug_title = data["debugTitle"] + make_title(data)
#     replacements = replacement_template()
#     replacements["DASHTITLE"] = dash_title
#     replacements["DEBUGTITLE"] = debug_title
#     replacements["IPHOSTA"] = data["hostA"]["IP"]
#     replacements["IPHOSTB"] = data["hostB"]["IP"]
#     replacements["VLANA"] = data["hostA"]["vlan"]
#     replacements["VLANB"] = data["hostB"]["vlan"]
#     replacements["IFNAMEHOSTA"] = data["hostA"]["interfaceName"]
#     replacements["IFNAMEHOSTB"] = data["hostB"]["interfaceName"]
#     replacements["IFINDEXSWITCHHOSTA"] = if_index1
#     replacements["IFINDEXSWITCHHOSTB"] = if_index2
#     replacements["DATAPLANEIPA"] = data["hostA"]["interfaceIP"]
#     replacements["DATAPLANEIPB"] = data["hostB"]["interfaceIP"]
#     replacements["NODENAMEA"] = data["hostA"]["nodeName"]
#     replacements["NODENAMEB"] = data["hostB"]["nodeName"]
    
        
#     for i in range(int(data['switchNum'])):
#         letter = chr(ord('A')+i) # A B C D ... 
#         replacements[f"IPSWITCH{letter}"] = data[f"switchData{letter}"]["target"]
#         replacements[f"SNMP{letter}NAME"]= data[f"switchData{letter}"]["job_name"]
#         replacements[f"SWITCH{letter}INVLAN"]= data[f"switchData{letter}"]["portIn"]["vlan"]
#         replacements[f"SWITCH{letter}OUTVLAN"]= data[f"switchData{letter}"]["portOut"]["vlan"]
#         replacements[f"NAMEIF{letter}IN"] = data[f"switchData{letter}"]["portIn"]["ifName"]
#         replacements[f"NAMEIF{letter}OUT"] = data[f"switchData{letter}"]["portOut"]["ifName"]
#         replacements[f"SWITCH{letter}OUTGOING"] = data[f"switchData{letter}"]["portOut"]["ifName"]
#         replacements[f"SWITCH{letter}INCOMING"] = data[f"switchData{letter}"]["portIn"]["ifName"]
#         replacements[f"SNMP{letter}HOSTIP"] = data[f"switchData{letter}"]["SNMPHostIP"]
#         replacements[f"MONITORVLAN{str(i+1)}"] = vlan_if_index[i]
#         replacements[f"MONITORVLAN{str(i+int(data['switchNum']))}"] = vlan_if_index[i+int(data['switchNum'])]

#     return replacements