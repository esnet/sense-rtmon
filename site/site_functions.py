import os
import yaml
import subprocess
import re

# configuration file path, system argument, the order it's in 
# e.g. python3 <file> abc.yml the order is 1
# e.g. python3 <file> <arg1> abc.yml the order is 2

def read_yml_file(path, sys_argv, order=1, go_back_folder_num=1):
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

# write to SNMP template
def write_template(data,template_path='./templates/generatorTemplate.yml',generator_file='generator.yml',order_letter=""):
    with open(template_path) as inGen, open(generator_file, 'w') as outGen:
        for line in inGen:
            outGen.write(line)
    oids = set(data[f'snmpMetrics{order_letter}']['oids'])
    # read all oids in first then add to generator file
    snip = ""
    for oid in oids:
        snip = snip + "      - " + str(oid) + "\n"
    with open(generator_file, 'r') as gen:
        text = gen.readlines()
    text[3] = snip
    with open(generator_file, 'w') as genOut:
        genOut.writelines(text)
        
    replacements = {'RETRY': str(data[f'snmpMetrics{order_letter}']['retries']),
                    'TIMEOUT': str(data[f'snmpMetrics{order_letter}']['scrapeTimeout']),
                    'COMMUNITYREADSTRING': str(data[f'snmpMetrics{order_letter}']['communityString'])}
    
    # Read in the file
    with open(generator_file, 'r') as file:
        filedata = file.read()
    # Replace the target string
    for k,v in replacements.items():
        filedata = filedata.replace(k, v)
    # Write the file out again
    with open(generator_file, 'w') as file:
        file.write(filedata)

# generate a snmp file
def generate_snmp_file(snmp_file='snmp.yml'):
    dir = str(os.getcwd())
    genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
    genCmd = "yes | cp -rfa generator.yml " + genLoc
    subprocess.run(genCmd, shell=True)
    print("Generating dynamic SNMP config file...")
    subprocess.run("./generator generate", shell=True, cwd=genLoc)
    subprocess.run(f"yes | cp -rfa snmp.yml ../../../../../{snmp_file}", shell=True, cwd=genLoc)
    print("Success! Configured custom SNMP Exporter container")
    print(f"{snmp_file} generated")

# copy paste mibs from librenms folder to parent mib folder
def download_mibs(mib_path):
    ne = input("Enter the name of the Network Element: ")
    if mib_path[0] != "/":
        mib_path = "/" + mib_path
    print(f"move all {ne} MIBS to mib folder")
    subprocess.run(f"yes | cp -rfa {mib_path}/librenms/mibs/{ne}/* ./", shell=True, cwd=mib_path)
    print("NEW SWITCH ADDED")
    
# generate a new snmp compose file in compose-files folder for each. One file for one snmp exporter
def generate_snmp_compose_file(path,switch_num):
    print(f"Generate a new docker compose file: added_snmp-docker-compose{str(switch_num)}.yml")
    print(f"Running on port: {str(9115+switch_num)}")
    new_compoes_file = f"""version: '3.8'
    services:
    snmp-exporter{switch_num}:
        image: prom/snmp-exporter
        volumes:
        - ../SNMPExporter/snmp{switch_num}.yml:/etc/snmp_exporter/snmp{switch_num}.yml
        ports:
        - {str(9115+int(switch_num))}:9116"""

    with open(f"{path}/added_snmp-docker-compose{str(switch_num)}.yml", 'w') as file:
        file.write(new_compoes_file)
        
# update crontab when SNMP exporter started
def update_snmp_crontab_script(path,switch_num,switch_ip):
    curl_flag = True
    cat_flag = True
    with open(f"{path}/push_snmp_exporter_metrics.sh") as inGen, open(f"{path}/temp_push_snmp_exporter_metrics.sh", 'w') as outGen:
        for line in inGen:
            if "curl -o " in line and curl_flag:
                new_line = re.sub("91.*/snmp", f"{str(9115+switch_num)}/snmp", line)
                new_line = re.sub("snmp_temp.txt", f"snmp_temp{str(switch_num)}.txt", new_line)
                new_line = re.sub("target=.*&", f"target={switch_ip}&", new_line)
                curl_flag = False
                outGen.write(new_line)
            elif "cat /" in line and cat_flag:
                new_line = re.sub("/snmp-exporter/target_switch/.*/instance/", f"/snmp-exporter{str(switch_num)}/target_switch/{switch_ip}/instance/", line)
                new_line = re.sub("snmp_temp.txt", f"snmp_temp{str(switch_num)}.txt", new_line)
                cat_flag = False
                outGen.write(new_line)        
            outGen.write(line)

    with open(f"{path}/push_snmp_exporter_metrics.sh",'w') as outGen, open(f"{path}/temp_push_snmp_exporter_metrics.sh") as inGen:
        for line in inGen:
            outGen.write(line)