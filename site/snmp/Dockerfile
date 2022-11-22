FROM rockylinux:9.0.20220720

# download dependencies 
RUN cd /home 
RUN yum -y update
RUN yum -y install python3 git make wget cronie pip gcc gcc-c++ make net-snmp net-snmp-utils net-snmp-libs net-snmp-devel
RUN wget https://dl.google.com/go/go1.19.3.linux-amd64.tar.gz
RUN rm -rf /usr/local/go && tar -C /usr/local -xzf go1.19.3.linux-amd64.tar.gz
RUN export PATH=$PATH:/usr/local/go/bin
RUN rm -rf go1.19.3.linux-amd64.tar.gz
RUN /usr/local/go/bin/go version
RUN GO111MODULE=auto /usr/local/go/bin/go get github.com/prometheus/snmp_exporter/generator
RUN cp -R /root/go/src /usr/local/go/bin/
RUN GO111MODULE=off /usr/local/go/bin/go build /root/go/src/github.com/prometheus/snmp_exporter/generator
RUN make mibs
RUN cd /home 
RUN pip3 install pyyaml

# these files will be changed depend the configuration file below
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/dynamic_start.sh
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/fill_start.py
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/snmp/run.sh

# !CUSTIMIZATION!
# you can replace the URL with a different configuration file!
RUN wget https://raw.githubusercontent.com/esnet/sense-rtmon/main/config_site/config.yml
# !CUSTIMIZATION! 

RUN mv *.yml /home/config.yml
RUN chmod +x *.sh
RUN mv dynamic_start.sh /home
RUN mv run.sh /home
RUN mv fill_start.py /home

ENTRYPOINT [ "/home/run.sh" ]