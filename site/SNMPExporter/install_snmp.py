import sys
import subprocess
import os
import yaml
sys.path.append("..") # Adds higher directory to python modules path.
import site_functions

print("INSTALL SNMP")
subprocess.run("sudo yum -y install p7zip p7zip-plugins gcc gcc-c++ make net-snmp net-snmp-utils net-snmp-libs net-snmp-devel", shell=True)
os.environ["PATH"] += os.pathsep + os.pathsep.join(["/usr/local/go/bin"])
dir = str(os.getcwd())
os.putenv("GOPATH", dir)
subprocess.run("go get github.com/prometheus/snmp_exporter/generator", shell=True)

print("Make Mibs")    
genLoc = dir + "/src/github.com/prometheus/snmp_exporter/generator"
genCmd = "yes | cp -rfa generator.yml " + genLoc
subprocess.run(genCmd, shell=True)
subprocess.run("go build", shell=True, cwd=genLoc)
# make mibs have been failing
# subprocess.run("make mibs", shell=True, cwd=genLoc)
subprocess.run("mkdir mibs", shell=True, cwd=genLoc)

print("Download private mibs")
mib_dir = genLoc + "/mibs"
os.chdir(mib_dir)
subprocess.run("git clone https://github.com/librenms/librenms.git",shell=True, cwd=mib_dir)
print("Check out librenms for private mibs https://github.com/librenms/librenms/tree/master/mibs\n")
subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/*-MIB ./", shell=True, cwd=mib_dir)

default_mibs = os.getenv("MIBDIRS")
subprocess.run(f"yes | cp -rfa /usr/share/snmp/mibs/* ./", shell=True, cwd=mib_dir)
subprocess.run(f"yes | cp -rfa {default_mibs}/* ./", shell=True, cwd=mib_dir)

print("Install Two Network Elements (to add more run /site/add_switch.py script)")
site_functions.download_mibs()
site_functions.download_mibs()

# ne = input("Enter the name of the Network Element: ")
# ne2 = input("Enter the name of the second Network Element (Press Enter to skip): ")

# print(f"move all {ne} MIBS to mib folder")
# subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/{ne}/* ./", shell=True, cwd=mib_dir)
# if ne2 != ne and ne2 != "":
#     print(f"move all {ne2} MIBS to mib folder")
#     subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/{ne2}/* ./", shell=True, cwd=mib_dir)

# subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/*/* ./", shell=True, cwd=mib_dir)
# subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/*/*/* ./", shell=True, cwd=mib_dir)

