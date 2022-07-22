import sys
import subprocess
import os

print("INSTALL SNMP")
print("Parsing config file...")
# Load yaml config file as dict
owd = os.getcwd()
os.chdir("..")
config_path = str(os.path.abspath(os.curdir))
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
            print(f"\n Config file {file_path} could not be found in the DynamicDashboard directory\n")
else: # default config file
    with open(infpth, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file {infpth} could not be found in the DynamicDashboard directory\n")

print("Collecting SNMP generator template...")
with open('generatorTemplate.yml') as inGen, open('generator.yml', 'w') as outGen:
        for line in inGen:
            outGen.write(line)
print("Reading SNMP OIDs/Interfaces/Scrape Duration/Scrape Time from config file...")

# SNMP scraps 1 switche
if(data['switchNum']) == 1:
    oids = set(data['snmpMetrics']['oids'])
    # read all oids in first then add to generator file
    snip = ""
    for oid in oids:
        snip = snip + "      - " + str(oid) + "\n"

    with open('generator.yml', 'r') as gen:
            text = gen.readlines()
    text[3] = snip
    with open('generator.yml', 'w') as genOut:
        genOut.writelines(text)
        
    replacements = {'RETRY': str(data['snmpMetrics']['retries']),
                    'TIMEOUT': str(data['snmpMetrics']['scrapeTimeout']),
                    'COMMUNITYREADSTRING': str(data['snmpMetrics']['communityString'])}
# SNMP scraps 2 switches
elif(data['switchNum']) == 2:
    oidsA = set(data['snmpMetricsA']['oids'])
    oidsB = set(data['snmpMetricsB']['oids'])
    # read all oids in first then add to generator file
    snipA = ""
    snipB = ""
    
    for oid in oidsA:
        snipA = snipA + "      - " + str(oid) + "\n"
    for oid in oidsB:
        snipB = snipB + "      - " + str(oid) + "\n"

    with open('generator.yml', 'r') as gen:
            text = gen.readlines()
    text[3] = snipA
    text[21] = snipB
    with open('generator.yml', 'w') as genOut:
        genOut.writelines(text)
        
    replacements = {'RETRY': str(data['snmpMetricsA']['retries']),
                    'TIMEOUT': str(data['snmpMetricsA']['scrapeTimeout']),
                    'COMMUNITYREADSTRING': str(data['snmpMetricsA']['communityString']),
                    'RETRY2': str(data['snmpMetricsB']['retries']),
                    'TIMEOUT2': str(data['snmpMetricsB']['scrapeTimeout']),
                    'COMMUNITYREADSTRING2': str(data['snmpMetricsB']['communityString'])}
elif(data['switchNum']) == 3:
    oidsA = set(data['snmpMetricsA']['oids'])
    oidsB = set(data['snmpMetricsB']['oids'])
    oidsC = set(data['snmpMetricsC']['oids'])
    # read all oids in first then add to generator file
    snipA = ""
    snipB = ""
    snipC = ""
    
    for oid in oidsA:
        snipA = snipA + "      - " + str(oid) + "\n"
    for oid in oidsB:
        snipB = snipB + "      - " + str(oid) + "\n"
    for oid in oidsC:
        snipC = snipC + "      - " + str(oid) + "\n"

    with open('generator.yml', 'r') as gen:
            text = gen.readlines()
    text[3] = snipA
    text[22] = snipB
    text[40] = snipC    
    with open('generator.yml', 'w') as genOut:
        genOut.writelines(text)
        
    replacements = {'RETRY': str(data['snmpMetricsA']['retries']),
                    'TIMEOUT': str(data['snmpMetricsA']['scrapeTimeout']),
                    'COMMUNITYREADSTRING': str(data['snmpMetricsA']['communityString']),
                    'RETRY2': str(data['snmpMetricsB']['retries']),
                    'TIMEOUT2': str(data['snmpMetricsB']['scrapeTimeout']),
                    'COMMUNITYREADSTRING2': str(data['snmpMetricsB']['communityString']),
                    'RETRY3': str(data['snmpMetricsC']['retries']),
                    'TIMEOUT3': str(data['snmpMetricsC']['scrapeTimeout']),
                    'COMMUNITYREADSTRING3': str(data['snmpMetricsC']['communityString'])}
    
else:
    print("invilad switch number")
    exit
    
    
# Read in the file
with open('generator.yml', 'r') as file:
    filedata = file.read()
# Replace the target string
for k,v in replacements.items():
    filedata = filedata.replace(k, v)
# Write the file out again
with open('generator.yml', 'w') as file:
    file.write(filedata)
    
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
print("Success! Configured custom SNMP Exporter container")
