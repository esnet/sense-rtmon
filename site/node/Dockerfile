FROM rockylinux:9.0.20220720

# download dependencies 
RUN cd /home 
RUN yum -y update
RUN yum -y install python3 git make wget cronie pip
RUN wget https://dl.google.com/go/go1.19.3.linux-amd64.tar.gz
RUN rm -rf /usr/local/go && tar -C /usr/local -xzf go1.19.3.linux-amd64.tar.gz
RUN export PATH=$PATH:/usr/local/go/bin
RUN rm -rf go1.19.3.linux-amd64.tar.gz
RUN /usr/local/go/bin/go version
RUN git clone https://github.com/prometheus/node_exporter.git
RUN mv node_exporter /home
RUN pip3 install pyyaml

# these files will be changed depend the configuration file below
RUN wget -O /home/dynamic_start.sh https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/node/dynamic_start.sh
RUN wget -O /home/run.sh https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/node/run.sh

RUN chmod +x /home/*.sh
ENTRYPOINT [ "/home/run.sh" ]