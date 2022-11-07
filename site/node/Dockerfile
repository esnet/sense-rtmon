FROM centos:latest

RUN cd /etc/yum.repos.d/
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

RUN cd /home 
RUN yum -y update
RUN yum -y install python3 git vim make wget cronie
RUN wget https://dl.google.com/go/go1.19.3.linux-amd64.tar.gz
RUN rm -rf /usr/local/go && tar -C /usr/local -xzf go1.19.3.linux-amd64.tar.gz
RUN export PATH=$PATH:/usr/local/go/bin
RUN rm -rf go1.19.3.linux-amd64.tar.gz
# RUN go env -w GO111MODULE=auto
RUN /usr/local/go/bin/go version
RUN git clone https://github.com/prometheus/node_exporter.git
RUN mv node_exporter /home
RUN pip3 install pyyaml


# RUN ./node_exporter &

# CMD /bin/bash
ENTRYPOINT [ "/home/run.sh" ]