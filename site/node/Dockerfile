FROM centos:latest

RUN cd /etc/yum.repos.d/
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

RUN yum -y update
RUN yum -y install python3 git vim make wget cronie
# subscription-manager
# RUN wget https://dl.google.com/go/go1.18.3.linux-amd64.tar.gz
# RUN export PATH=${PATH}:/usr/local/go/bin
# RUN tar -C /usr/local -xzf go1.18.3.linux-amd64.tar.gz
# RUN rm -rf go1.18.3.linux-amd64.tar.gz
# RUN go env -w GO111MODULE=auto
# RUN go version
# RUN cd home
# RUN git clone https://github.com/prometheus/node_exporter.git

# RUN ./node_exporter &

# CMD /bin/bash
ENTRYPOINT [ "/home/run.sh" ]