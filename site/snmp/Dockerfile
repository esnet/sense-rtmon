FROM rockylinux:9.0.20220720

# install dependencies 
RUN cd /home 
RUN yum -y update
RUN yum -y install python3 git make wget cronie pip
# RUN yum -y install p7zip p7zip-plugins
RUN yum -y install make gcc gcc-c++ net-snmp net-snmp-utils net-snmp-libs net-snmp-devel
RUN pip3 install pyyaml

# install Go
RUN wget https://dl.google.com/go/go1.19.3.linux-amd64.tar.gz
RUN rm -rf /usr/local/go && tar -C /usr/local -xzf go1.19.3.linux-amd64.tar.gz
RUN export PATH=$PATH:/usr/local/go/bin
RUN rm -rf go1.19.3.linux-amd64.tar.gz
RUN /usr/local/go/bin/go version

# install official SNMP Exporter !!!!!!!!!!!!!! GITHUB PAGE READ
RUN git clone https://github.com/prometheus/snmp_exporter.git /home/snmp_exporter

# install SNMP binary release 
# !CUSTIMIZATION!
RUN wget https://github.com/prometheus/snmp_exporter/releases/download/v0.21.0/snmp_exporter-0.21.0.linux-amd64.tar.gz
# !CUSTIMIZATION!
RUN tar -xvzf snmp_exporter-0.21.0.linux-amd64.tar.gz 
RUN rm -rf snmp_exporter-0.21.0.linux-amd64.tar.gz
RUN mv snmp_exporter-0.21.0.linux-amd64 /home

# install librenms library which contains all mibs that's needed
RUN git clone https://github.com/librenms/librenms.git /home/librenms

# these files will be changed depend the configuration file below
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/dynamic_start.sh
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/fill_start.py
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/run.sh
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/generator_template.yml
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/fill_template.py
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/snmp_functions.py

# !CUSTIMIZATION!
# you can replace the URL with a different configuration file!
# RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/config_site/config.yml
# run environmental variables instead of config files, per run variables should be given at runtime
# configuration files can be variables themsleves, run time variable
# multi use for multi runs more dynamic situation
# !CUSTIMIZATION! 

# move all wget files to /home directory
RUN mv generator_template.yml /home
RUN mv *.yml /home/config.yml
RUN chmod +x *.sh
RUN mv *.sh /home
RUN mv *.py /home

ENTRYPOINT [ "/home/run.sh" ]