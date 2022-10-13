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

# file naming 
for i in range(int(data['switchNum'])):
    letter = chr(ord('A')+1+i)
    site_functions.write_template(data,order_letter=letter)
    site_functions.generate_snmp_file(f"snmp{str(i+1)}.yml")
    
else:
    print("invilad switch number")
    exit