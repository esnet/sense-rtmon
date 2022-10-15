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
subprocess.run("mkdir mibs", shell=True, cwd=genLoc)
# make mibs have been failing
# subprocess.run("make mibs", shell=True, cwd=genLoc)

print("Download private mibs for ALL network elements in librenms")
mib_dir = genLoc + "/mibs"
os.chdir(mib_dir)
subprocess.run("git clone https://github.com/librenms/librenms.git",shell=True, cwd=mib_dir)
print("Check out librenms for private mibs https://github.com/librenms/librenms/tree/master/mibs\n")
subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/*-MIB ./", shell=True, cwd=mib_dir)
subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/*/* ./", shell=True, cwd=mib_dir)
subprocess.run(f"yes | cp -rfa {mib_dir}/librenms/mibs/*/*/* ./", shell=True, cwd=mib_dir)
subprocess.run(f"yes | cp -rfa /usr/share/snmp/mibs/* ./", shell=True, cwd=mib_dir)

print(f"\n\nset MIBDIRS to MIBDIRS={mib_dir}")
# os.environ["MIBDIRS"]= "abc"
subprocess.run(f"sudo export MIBDIRS=$MIBDIRS:{mib_dir}", shell=True, cwd=genLoc)
print("SNMP and MIBs install complete.")