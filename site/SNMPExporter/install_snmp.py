import sys
import subprocess
import os
import yaml
# from .. import site_functions

# # read yml file
# data,file_name = site_functions.read_yml_file("config_site",sys.argv,1,2)

print("INSTALL SNMP")
print("Parsing config file...")
# Load yaml config file as dict
owd = os.getcwd()
os.chdir("..")
os.chdir("..")
config_path = str(os.path.abspath(os.curdir)) +"/config_site"
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
        write_template(letter="C")
        generate_snmp_file("snmp2.yml")
    
else:
    print("invilad switch number")
    exit
    
    
subprocess.run("sudo yum -y install p7zip p7zip-plugins gcc gcc-c++ make net-snmp net-snmp-utils net-snmp-libs net-snmp-devel", shell=True)
os.environ["PATH"] += os.pathsep + os.pathsep.join(["/usr/local/go/bin"])
dir = str(os.getcwd())
os.putenv("GOPATH", dir)
subprocess.run("go get github.com/prometheus/snmp_exporter/generator", shell=True)
genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
genCmd = "yes | cp -rfa generator.yml " + genLoc
subprocess.run(genCmd, shell=True)
subprocess.run("go build", shell=True, cwd=genLoc)

subprocess.run("make mibs", shell=True, cwd=genLoc)
subprocess.run("export MIBDIRS=mibs", shell=True, cwd=genLoc)
print("Success! Configured custom SNMP Exporter container\n\n")

# download private mibs    
mib_dir = genLoc + "/mibs"
os.chdir(mib_dir)
subprocess.run("git clone https://github.com/librenms/librenms.git",shell=True, cwd=mib_dir)
print("To download private MIBs please find the network element brand on this list https://github.com/librenms/librenms/tree/master/mibs\n")
subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/*-MIB ./", shell=True, cwd=mib_dir)

ne = input("Enter the name of the Network Element: ")
ne2 = input("Enter the name of the second Network Element (Press Enter to skip): ")
ne3 = input("Enter the name of the third Network Element: (Press Enter to skip)")

print(f"move all {ne} MIBS to mib folder")
subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/{ne}/* ./", shell=True, cwd=mib_dir)
if ne2 != ne and ne2 != "":
    print(f"move all {ne2} MIBS to mib folder")
    subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/{ne2}/* ./", shell=True, cwd=mib_dir)
if ne2 != ne3 and ne3 != "":
    print(f"move all {ne3} MIBS to mib folder")
    subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/{ne3}/* ./", shell=True, cwd=mib_dir)

subprocess.run(f"yes | cp -rfa /usr/share/snmp/mibs/* ./", shell=True, cwd=mib_dir)
print("SNMP and MIBs install complete.")
# subprocess.run("./generator generate", shell=True, cwd=genLoc)
# subprocess.run("yes | cp -rfa snmp.yml ../../../../../", shell=True, cwd=genLoc)
# print("Success! Configured custom SNMP Exporter container")
