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

# SNMP scraps 1 switch
if(data['switchNum']) == 1:
    site_functions.write_template(data)
    site_functions.generate_snmp_file()

# SNMP scraps 2 switches
elif(data['switchNum']) >= 2:
    # first switch generate snmp.yml file
    site_functions.write_template(data,letter="A")
    site_functions.generate_snmp_file()

    # Second switch generate snmp.yml file
    site_functions.write_template(data,letter="B")
    site_functions.generate_snmp_file("snmp2.yml")

    # Third switch generate snmp.yml file
    if(data['switchNum']) >= 3:
        site_functions.write_template(data,letter="C")
        site_functions.generate_snmp_file("snmp2.yml")
    
else:
    print("invilad switch number")
    exit