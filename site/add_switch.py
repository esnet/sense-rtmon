import sys
import subprocess
import os
import re

# print("ADD SNMP EXPORTER AND SWITCH")
# print("To download private MIBs please find the network element brand on this list https://github.com/librenms/librenms/tree/master/mibs\n")
# ne = input("Enter the name of the Network Element: ")
# switch_ip = input("Enter the IP of the Network Element: ")
# switch_ip = switch_ip.strip()
# community_string = input("Enter the community string of the Network Element: ")
# switch_num = input("Enter the number of existing SNMP exporter (2 SNMP exporters are running by default, it should be 3 or greater. run: $docker ps to check): ")
# switch_num = str(switch_num.strip())
# new_oid = input("Enter oids seperated by space (e.g.: 1.3.6.1.2.1.17.4.3.1.1 1.3.6.1.2.1.31   or   dot1dTpFdbAddress ifMIB): ")
# oid_list = new_oid.split()

# # download private mibs
# dir = str(os.getcwd())
# genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
# mib_dir = genLoc + "/mibs"
# print(f"move all {ne} MIBS to mib folder")
# subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/{ne}/* ./", shell=True, cwd=mib_dir)
# print("NEW SWITCH ADDED")

# def write_template(template_path='./templates/generatorTemplate.yml',generator_file='generator.yml'):
#     with open(template_path) as inGen, open(generator_file, 'w') as outGen:
#         for line in inGen:
#             outGen.write(line)
#     oids = set(oid_list)
#     # read all oids in first then add to generator file
#     snip = ""
#     for oid in oids:
#         snip = snip + "      - " + str(oid) + "\n"
#     with open(generator_file, 'r') as gen:
#         text = gen.readlines()
#     text[3] = snip
#     with open(generator_file, 'w') as genOut:
#         genOut.writelines(text)
        
#     replacements = {'RETRY': 3,
#                     'TIMEOUT': "5s",
#                     'COMMUNITYREADSTRING': community_string}
    
#     # Read in the file
#     with open(generator_file, 'r') as file:
#         filedata = file.read()
#     # Replace the target string
#     for k,v in replacements.items():
#         filedata = filedata.replace(k, v)
#     # Write the file out again
#     with open(generator_file, 'w') as file:
#         file.write(filedata)

# def generate_snmp_file(snmp_file='snmp.yml'):
#     dir = str(os.getcwd())
#     genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
#     genCmd = "yes | cp -rfa generator.yml " + genLoc
#     subprocess.run(genCmd, shell=True)
#     print("Generating dynamic SNMP config file...")
#     subprocess.run("./generator generate", shell=True, cwd=genLoc)
#     subprocess.run(f"yes | cp -rfa snmp.yml ../../../../../{snmp_file}", shell=True, cwd=genLoc)
#     print("Success! Configured custom SNMP Exporter container")

# print(f"Generate a new docker compose file: snmp-docker-compose{switch_num}.yml")
# print(f"Running on port: 911{str(5+int(switch_num))}")
# new_compoes_file = f"""version: '3.8'
# services:
#   snmp-exporter2:
#     image: prom/snmp-exporter
#     volumes:
#       - ../SNMPExporter/snmp{switch_num}.yml:/etc/snmp_exporter/snmp{switch_num}.yml
#     ports:
#       - 911{str(5+int(switch_num))}:9116"""

# with open(f"snmp-docker-compose{switch_num}.yml", 'w') as file:
#     file.write(new_compoes_file)

# # add new target to crontab executing script push_snmp_exporter_metrics.sh
# curl_flag = True
# cat_flag = True
# with open("crontabs/push_snmp_exporter_metrics.sh") as inGen, open("crontabs/temp_push_snmp_exporter_metrics.sh ", 'w') as outGen:
#     for line in inGen:
#         if "curl -o " in line and curl_flag:
#             new_line = re.sub("9116", f"911{str(5+int(switch_num))}", line)
#             new_line = re.sub("=.*&", f"{switch_ip}", line)
#             curl_flag = False
#             outGen.write(new_line)
#         elif "cat /" in line and curl_flag:
#             new_line = re.sub("/snmp-exporter/target_switch/172.16.1.1/instance/", f"/snmp-exporter{switch_num}/target_switch/{switch_ip}/instance/", line)
#             new_line = re.sub("=.*&", f"{switch_ip}", line)
#             cat_flag = False
#             outGen.write(new_line)        
#         outGen.write(line)


# # writing SNMP and generate snmp.yml files
# write_template
# generate_snmp_file(f"snmp{switch_num}.yml")

curl_flag = True
cat_flag = True
with open("crontabs/push_snmp_exporter_metrics.sh") as inGen, open("crontabs/temp_push_snmp_exporter_metrics.sh ", 'w') as outGen:
    for line in inGen:
        if "curl -o " in line and curl_flag:
            new_line = re.sub("9116", f"9118", line)
            new_line = re.sub("=.*&", f"111", line)
            curl_flag = False
            outGen.write(new_line)
        elif "cat /" in line and curl_flag:
            new_line = re.sub("/snmp-exporter/target_switch/172.16.1.1/instance/", f"/snmp-exporter3/target_switch/111/instance/", line)
            new_line = re.sub("=.*&", f"111", line)
            cat_flag = False
            outGen.write(new_line)        
        outGen.write(line)