import sys
import subprocess
import os
import re
import site_functions

print("\n\nADD SNMP EXPORTER AND SWITCH")
print("!!   Before running this script, snmp exporter needs to downloaded, and SNMP exporters are started in start.sh   !!")
print("To download private MIBs please find the network element brand on this list https://github.com/librenms/librenms/tree/master/mibs\n\n")
dir = str(os.getcwd())
genLoc = dir + "/SNMPExporter/src/github.com/prometheus/snmp_exporter/generator"
site_functions.download_mibs(f"{genLoc}/mibs")

switch_ip = input("Enter the IP of the Network Element: ")
switch_ip = switch_ip.strip()
community_string = input("Enter the community string of the Network Element: ")
# find the number of existing SNMP exporter
SNMP_files = os.listdir("./SNMPExporter")
snmp_yml = [x for x in SNMP_files if "snmp" in x and ".yml" in x] 
snmp_yml.sort()
largest_num = ""
if len(snmp_yml) > 0:
    for letter in snmp_yml[-1]:
        if letter.isdigit():
            largest_num = largest_num + letter
else:
    largest_num = 0
    
switch_num = int(largest_num)+1
new_oid = input("Enter oids separated by space (e.g.: 1.3.6.1.2.1.17.4.3.1.1 1.3.6.1.2.1.31   or   dot1dTpFdbAddress ifMIB): ")
oid_list = new_oid.split()

# make new SNMP file
data = {"snmpMetrics": 
   {"retries":3, 
    "scrapeTimeout":"5s",
    "communityString":community_string,
    "oids":oid_list
    }
}

site_functions.write_template(data,template_path="./SNMPExporter/templates/generatorTemplate.yml",generator_file="./SNMPExporter/generator.yml")

os.chdir("./SNMPExporter")
site_functions.generate_snmp_file(f"snmp{switch_num}.yml")
os.chdir("..")

# Make new docker file
site_functions.generate_snmp_compose_file("./compose-files",switch_num)

# add new target to crontab executing script push_snmp_exporter_metrics.sh
site_functions.update_snmp_crontab_script("crontabs",switch_num,switch_ip)    
print("COMPOSE NEW SNMP EXPORTER:")

subprocess.run(f"docker compose -f ./compose-files/snmp-docker-compose{str(switch_num)}.yml up -d", shell=True)