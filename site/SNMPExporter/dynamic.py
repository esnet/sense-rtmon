import yaml
import sys
import subprocess
import os
sys.path.append("..") # Adds higher directory to python modules path.
import site_functions

print("Parsing config file...")
data,file_name = site_functions.read_yml_file("config_site",sys.argv,1,2)
print("Collecting SNMP generator template...")
print("Reading SNMP OIDs/Interfaces/Scrape Duration/Scrape Time from config file...")

mib_dir = f"{str(os.getcwd())}/src/github.com/prometheus/snmp_exporter/generator/mibs"
print(f"\n\nset MIBDIRS to MIBDIRS={mib_dir}")
# default_mibdirs = os.getenv["MIBDIRS"]
os.environ["MIBDIRS"]= f"{mib_dir}"
# subprocess.run(f"export MIBDIRS=$MIBDIRS:{mib_dir}", shell=True, cwd=mib_dir)
subprocess.run(f"echo $MIBDIRS", shell=True, cwd=mib_dir)

print("SNMP and MIBs install complete.")

# file naming 
for i in range(int(data['switchNum'])):
    letter = chr(ord('A')+i) # A B C D ... 
    site_functions.write_template(data,order_letter=letter)
    site_functions.generate_snmp_file(f"snmp{str(i+1)}.yml") # snmp1.yml snmp2.yml ...
