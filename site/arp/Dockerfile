FROM rockylinux

# download dependencies 
RUN cd /home 
RUN yum -y update
RUN yum -y install python3 git make wget cronie pip net-tools
RUN pip install pyyaml pyyaml requests prometheus_client

# these files will be changed depend the configuration file below
RUN wget -O /home/dynamic_start.sh https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/arp/dynamic_start.sh
RUN wget -O /home/run.sh https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/arp/run.sh
RUN wget -O /home/arp_exporter.py https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/arp/arp_exporter.py
RUN wget -O /home/convert_arp.py https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/arp/convert_arp.py
RUN wget -O /home/class_arp_exporter.py https://raw.githubusercontent.com/esnet/sense-rtmon/main/site/arp/class_arp_exporter.py
RUN chmod +x /home/*.sh

ENTRYPOINT [ "/home/run.sh" ]