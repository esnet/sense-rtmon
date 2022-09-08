import yaml
import sys
import subprocess
import os
print("Parsing config file...")
# Load yaml config file as dict
owd = os.getcwd()
os.chdir("..")
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config"
infpth = config_path + "/config.yml"
os.chdir(owd)
data = {}
# argument given
if len(sys.argv) > 1:
    file_name = str(sys.argv[1])
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
print("Collecting SNMP generator template...")
print("Reading SNMP OIDs/Interfaces/Scrape Duration/Scrape Time from config file...")

def write_template(template_path='./templates/generatorTemplate.yml',generator_file='generator.yml',letter=""):
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


# SNMP scraps 1 switch
if(data['switchNum']) == 1:
    write_template
    generate_snmp_file

# SNMP scraps 2 switches
elif(data['switchNum']) >= 2:
    # first switch generate snmp.yml file
    write_template(letter="A")
    generate_snmp_file()

    # Second switch generate snmp.yml file
    write_template(letter="B")
    generate_snmp_file("snmp2.yml")

    # Third switch generate snmp.yml file
    if(data['switchNum']) >= 3:
        write_template(letter="B")
        generate_snmp_file("snmp2.yml")
    

else:
    print("invilad switch number")
    exit