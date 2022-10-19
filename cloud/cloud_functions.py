import json
import os
import yaml
import sys
import re 
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
    # alternative title naming
    dash_title = str(data['dashTitle']) + title
    debug_title = str(data['debugTitle']) + title
    return title

def fill_replacement(data):
    dash_title = str(data['dashTitle']) + make_title(data)
    debug_title = str(data['debugTitle']) + make_title(data)
    replacements = replacement_template()
    replacements["DASHTITLE"] = dash_title
    replacements["DEBUGTITLE"] = debug_title
    replacements["IPHOSTA"] = str(data['hostA']['IP'])
    replacements["IPHOSTB"] = str(data['hostB']['IP'])
    
    
    #         'IPHOSTA': str(data['hostA']['IP']), 
    #     'IPHOSTB': str(data['hostB']['IP']),
    #     'VLANA': str(data['hostA']['vlan']),
    #     'VLANB': str(data['hostB']['vlan']),
    #     'MONITORVLAN1': str(vlan_if_index1),
    #     'MONITORVLAN2': str(vlan_if_index2),
    #     'MONITORVLAN3': str(vlan_if_index3),
    #     'IFNAMEHOSTA': str(data['hostA']['interfaceName']),
    #     'IFNAMEHOSTB': str(data['hostB']['interfaceName']),
    #     'SNMP1HOSTIP': str(data['switchDataA']['SNMPHostIP']),
    #     'SNMP2HOSTIP': str(data['switchDataB']['SNMPHostIP']),
    #     'SNMP3HOSTIP': str(data['switchDataC']['SNMPHostIP']),
    #     'SNMP4HOSTIP': str(data['switchDataD']['SNMPHostIP']),
    #     'IFINDEXSWITCHHOSTA': str(if_index1),
    #     'SWITCHAOUTGOING': str(data['switchDataA']['portOut']['ifName']),
    #     'SWITCHAINCOMING': str(data['switchDataA']['portIn']['ifName']),
    #     'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifName']),
    #     'SWITCHBOUTGOING': str(data['switchDataB']['portOut']['ifName']),
    #     'SWITCHCINCOMING': str(data['switchDataC']['portIn']['ifName']),
    #     'SWITCHCOUTGOING': str(data['switchDataC']['portOut']['ifName']),
    #     'SWITCHDINCOMING': str(data['switchDataD']['portIn']['ifName']),
    #     'SWITCHDOUTGOING': str(data['switchDataD']['portOut']['ifName']),
    #     'IFINDEXSWITCHHOSTB': str(if_index2),
    #     'NAMEIFAIN': str(data['switchDataA']['portIn']['ifName']),
    #     'NAMEIFAOUT': str(data['switchDataA']['portOut']['ifName']),
    #     'NAMEIFBIN': str(data['switchDataB']['portIn']['ifName']),
    #     'NAMEIFBOUT': str(data['switchDataB']['portOut']['ifName']),
    #     'NAMEIFCIN': str(data['switchDataC']['portIn']['ifName']),
    #     'NAMEIFCOUT': str(data['switchDataC']['portOut']['ifName']),
    #     'NAMEIFDIN': str(data['switchDataD']['portIn']['ifName']),
    #     'NAMEIFDOUT': str(data['switchDataD']['portOut']['ifName']),
    #     'DATAPLANEIPA': str(data['hostA']['interfaceIP']),
    #     'DATAPLANEIPB': str(data['hostB']['interfaceIP']),
    #     'NODENAMEA': str(data['hostA']['nodeName']),
    #     'NODENAMEB': str(data['hostB']['nodeName']),
    #     'IPSWITCHA': str(data['switchDataA']['target']),
    #     'IPSWITCHB': str(data['switchDataB']['target']),
    #     'IPSWITCHC': str(data['switchDataC']['target']),
    #     'IPSWITCHD': str(data['switchDataD']['target']),
    #     'SNMPANAME': str(data['switchDataA']['job_name']),
    #     'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
    #     'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
    #     'SWITCHBINVLAN': str(data['switchDataB']['portIn']['vlan']),
    #     'SWITCHBOUTVLAN': str(data['switchDataB']['portOut']['vlan']),
    #     'SWITCHCINVLAN': str(data['switchDataC']['portIn']['vlan']),
    #     'SWITCHCOUTVLAN': str(data['switchDataC']['portOut']['vlan']),
    #     'SWITCHDINVLAN': str(data['switchDataD']['portIn']['vlan']),
    #     'SWITCHDOUTVLAN': str(data['switchDataD']['portOut']['vlan']),
    #     'DASHTITLE': f" {str(data['dashTitle'])} 4 switches {timeTxt}",
    #     'DEBUGTITLE': f" {str(data['debugTitle'])} 4 switches {timeTxt}"
    
    # replacements = {

    # 'SWITCHBINCOMING': str(data['switchDataB']['portIn']['ifName']),
    # 'SWITCHBOUTGOING': str(data['switchDataB']['portOut']['ifName']),
    # 'SWITCHCINCOMING': str(data['switchDataC']['portIn']['ifName']),
    # 'SWITCHCOUTGOING': str(data['switchDataC']['portOut']['ifName']),
    # 'SWITCHDINCOMING': str(data['switchDataD']['portIn']['ifName']),
    # 'SWITCHDOUTGOING': str(data['switchDataD']['portOut']['ifName']),
    # 'IFINDEXSWITCHHOSTB': str(if_index2),
    # 'NAMEIFAIN': str(data['switchDataA']['portIn']['ifName']),
    # 'NAMEIFAOUT': str(data['switchDataA']['portOut']['ifName']),
    # 'NAMEIFBIN': str(data['switchDataB']['portIn']['ifName']),
    # 'NAMEIFBOUT': str(data['switchDataB']['portOut']['ifName']),
    # 'NAMEIFCIN': str(data['switchDataC']['portIn']['ifName']),
    # 'NAMEIFCOUT': str(data['switchDataC']['portOut']['ifName']),
    # 'NAMEIFDIN': str(data['switchDataD']['portIn']['ifName']),
    # 'NAMEIFDOUT': str(data['switchDataD']['portOut']['ifName']),
    # 'DATAPLANEIPA': str(data['hostA']['interfaceIP']),
    # 'DATAPLANEIPB': str(data['hostB']['interfaceIP']),
    # 'NODENAMEA': str(data['hostA']['nodeName']),
    # 'NODENAMEB': str(data['hostB']['nodeName']),
    # 'IPSWITCHA': str(data['switchDataA']['target']),
    # 'IPSWITCHB': str(data['switchDataB']['target']),
    # 'IPSWITCHC': str(data['switchDataC']['target']),
    # 'IPSWITCHD': str(data['switchDataD']['target']),
    # 'SNMPNAMEA': str(data['switchDataA']['job_name']),
    # 'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
    # 'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan']),
    # 'SWITCHBINVLAN': str(data['switchDataB']['portIn']['vlan']),
    # 'SWITCHBOUTVLAN': str(data['switchDataB']['portOut']['vlan']),
    # 'SWITCHCINVLAN': str(data['switchDataC']['portIn']['vlan']),
    # 'SWITCHCOUTVLAN': str(data['switchDataC']['portOut']['vlan']),
    # 'SWITCHDINVLAN': str(data['switchDataD']['portIn']['vlan']),
    # 'SWITCHDOUTVLAN': str(data['switchDataD']['portOut']['vlan']),
    # 'DASHTITLE': f" {str(data['dashTitle'])} 4 switches {timeTxt}",
    # 'DEBUGTITLE': f" {str(data['debugTitle'])} 4 switches {timeTxt}",
    

    # 'NAMEIFSWITCHA': str(data['hostA']['switchPort']['ifName']),
    # 'NAMEIFSWITCHB': str(data['hostB']['switchPort']['ifName']),
    # 'VLANA': str(data['hostA']['vlan']),
    # 'VLANB': str(data['hostB']['vlan']),
    # 'SWITCHIF': str(data['switchDataA']['switchif']),
    # 'SWITCHAINVLAN': str(data['switchDataA']['portIn']['vlan']),
    # 'SWITCHAOUTVLAN': str(data['switchDataA']['portOut']['vlan'])}

    return replacements