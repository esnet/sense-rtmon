FROM rockylinux:9.0.20220720

# download dependencies 
RUN cd /home 
RUN yum -y update
RUN yum -y install python3 git make wget cronie pip net-tools
RUN pip install pyyaml pyyaml requests prometheus_client

# these files will be changed depend the configuration file below
RUN wget -O /home/dynamic_start.sh https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/tcp/dynamic_start.sh
RUN wget -O /home/run.sh https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/tcp/run.sh
RUN wget -O /home/arp_exporter.py https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/tcp/tcp_exporter.py
RUN wget -O /home/convert_arp.py https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/tcp/
RUN wget -O /home/convert_arp.py https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/tcp/
RUN chmod +x /home/*.sh

ENTRYPOINT [ "/home/run.sh" ]