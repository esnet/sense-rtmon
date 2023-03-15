FROM rockylinux:9.1

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
RUN pip3 install pyyaml paho-mqtt requests

# these files will be changed depend the configuration file below
RUN wget -O /home/dynamic_start.sh https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/node_mqtt/dynamic_start.sh
RUN wget -O /home/run.sh https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/node_mqtt/run.sh
RUN wget -O /home/client.py https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/node_mqtt/client.py
RUN wget -O /home/update.py https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/node_mqtt/update.py

RUN chmod +x /home/*.sh
ENTRYPOINT [ "/home/run.sh" ]