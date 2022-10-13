import os
import yaml
import subprocess

# configuration file path, system argument, the order it's in 
# e.g. python3 <file> abc.yml the order is 1
# e.g. python3 <file> <arg1> abc.yml the order is 2

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

# write to SNMP template
def write_template(data,template_path='./templates/generatorTemplate.yml',generator_file='generator.yml',letter=""):
    with open(template_path) as inGen, open(generator_file, 'w') as outGen:
        for line in inGen:
            outGen.write(line)
    oids = set(data[f'snmpMetrics{letter}']['oids'])
    # read all oids in first then add to generator file
    snip = ""
    for oid in oids:
        snip = snip + "      - " + str(oid) + "\n"
    with open(generator_file, 'r') as gen:
        text = gen.readlines()
    text[3] = snip
    with open(generator_file, 'w') as genOut:
        genOut.writelines(text)
        
    replacements = {'RETRY': str(data[f'snmpMetrics{letter}']['retries']),
                    'TIMEOUT': str(data[f'snmpMetrics{letter}']['scrapeTimeout']),
                    'COMMUNITYREADSTRING': str(data[f'snmpMetrics{letter}']['communityString'])}
    
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
    # subprocess.run("yes | cp -rfa snmp.yml ../../../../../", shell=True, cwd=genLoc)
    print("Success! Configured custom SNMP Exporter container")
