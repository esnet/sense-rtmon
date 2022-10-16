import sys
import subprocess
import os
import re
import site_functions

print("\n\nADD SNMP EXPORTER AND SWITCH")
print("!!   Before running this script, snmp exporter needs to downloaded, start.sh is ran, and crontab is created   !!")
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
   {"retries":"3s", 
    "scrapeTimeout":"5s",
    "communityString":community_string,
    "oids":oid_list
    }
}

site_functions.write_template(data,template_path="./SNMPExporter/templates/generatorTemplate.yml",generator_file="./SNMPExporter/generator.yml")

os.chdir("./SNMPExporter")
site_functions.generate_snmp_file(f"snmp{switch_num}.yml")
os.chdir("..")

# genCmd = "yes | cp -rfa ./SNMPExporter/generator.yml " + genLoc
# subprocess.run(genCmd, shell=True)
# print("Generating dynamic SNMP config file...")
# subprocess.run("./generator generate", shell=True, cwd=genLoc)
# subprocess.run(f"yes | cp -rfa snmp.yml ../../../../../snmp{switch_num}.yml", shell=True, cwd=genLoc)
# print("Success! Configured custom SNMP Exporter container")
# print(f"snmp{switch_num}.yml generated")

# Make new docker file
print(f"Generate a new docker compose file: added_snmp-docker-compose{switch_num}.yml")
print(f"Running on port: 911{str(5+int(switch_num))}")
new_compoes_file = f"""version: '3.8'
services:
  snmp-exporter{switch_num}:
    image: prom/snmp-exporter
    volumes:
      - ../SNMPExporter/snmp{switch_num}.yml:/etc/snmp_exporter/snmp{switch_num}.yml
    ports:
      - 911{str(5+int(switch_num))}:9116"""

with open(f"./compose-files/added_snmp-docker-compose{switch_num}.yml", 'w') as file:
    file.write(new_compoes_file)

# add new target to crontab executing script push_snmp_exporter_metrics.sh
curl_flag = True
cat_flag = True
with open("crontabs/push_snmp_exporter_metrics.sh") as inGen, open("crontabs/temp_push_snmp_exporter_metrics.sh", 'w') as outGen:
    for line in inGen:
        if "curl -o " in line and curl_flag:
            new_line = re.sub("9116", f"911{str(5+int(switch_num))}", line)
            new_line = re.sub("snmp_temp.txt", f"snmp_temp{switch_num}.txt", new_line)
            new_line = re.sub("=.*&", f"={switch_ip}&", new_line)
            curl_flag = False
            outGen.write(new_line)
        elif "cat /" in line and cat_flag:
            new_line = re.sub("/snmp-exporter/target_switch/.*/instance/", f"/snmp-exporter{switch_num}/target_switch/{switch_ip}/instance/", line)
            new_line = re.sub("snmp_temp.txt", f"snmp_temp{switch_num}.txt", new_line)
            cat_flag = False
            outGen.write(new_line)        
        outGen.write(line)

with open("crontabs/push_snmp_exporter_metrics.sh",'w') as outGen, open("crontabs/temp_push_snmp_exporter_metrics.sh") as inGen:
    for line in inGen:
        outGen.write(line)
    
print("COMPOSE NEW SNMP EXPORTER:")

subprocess.run(f"docker compose -f ./compose-files/added_snmp-docker-compose{switch_num}.yml up -d", shell=True)