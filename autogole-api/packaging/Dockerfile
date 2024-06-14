FROM opensciencegrid/software-base:23-al8-release

RUN yum -y install wget epel-release && \
    yum -y install git python3 python3-pyyaml python3-devel python3-pip gcc openssl-devel cronie python3-pyOpenSSL fetch-crl && \
    yum clean all

RUN mkdir -p /opt/ && \
    mkdir -p /srv/ && \
    mkdir -p /etc/rtmon/templates/ && \
    mkdir -p /var/log/rtmon/ && \
    mkdir -p /etc/grid-security/certificates/

# Install pip packages
RUN pip3 install setuptools --upgrade
RUN pip3 install wheel

# Install SENSE Py Client
RUN git clone https://github.com/sdn-sense/sense-o-py-client.git /opt/sense-o-py-client && \
    cd /opt/sense-o-py-client && pip3 install -r requirements.txt && pip3 install .

# Install RTMON (TODO, replace to ESnet repo once merged)
RUN git clone https://github.com/juztas/sense-rtmon.git /opt/sense-rtmon && \
    cd /opt/sense-rtmon/autogole-api/ && pip3 install -r requirements.txt && pip3 install . && \
    cp src/templates/* /etc/rtmon/templates/

RUN wget https://raw.githubusercontent.com/sdn-sense/rm-configs/master/CAs/SiteRM.pem -O /etc/grid-security/certificates/e52ac827.0

ADD files/etc/supervisord.d/10-server.conf /etc/supervisord.d/10-server.conf

# Get latest CA's
RUN fetch-crl || echo "Supress warnings."
