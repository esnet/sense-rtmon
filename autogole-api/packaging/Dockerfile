FROM opensciencegrid/software-base:23-al8-release

# hadolint ignore=DL3033
RUN yum -y install wget epel-release && \
    yum -y install git python3 python3-pyyaml python3-devel python3-pip gcc openssl-devel cronie python3-pyOpenSSL fetch-crl graphviz && \
    yum clean all

# Create necessary directories
WORKDIR /opt
RUN mkdir -p /srv/icons/ /etc/rtmon/templates/ /var/log/rtmon/ /etc/grid-security/certificates/

# Upgrade PIP SetupTools and wheek and Install SENSE Py Client
WORKDIR /opt/sense-o-py-client
RUN pip3 install --no-cache-dir --upgrade setuptools==58.2.0 wheel==0.37.0 && \
    git clone https://github.com/sdn-sense/sense-o-py-client.git . && \
    pip3 install --no-cache-dir -r requirements.txt && pip3 install --no-cache-dir .

# Install RTMON
WORKDIR /opt/sense-rtmon
RUN git clone https://github.com/esnet/sense-rtmon.git . \
WORKDIR /opt/sense-rtmon/autogole-api
RUN pip3 install --no-cache-dir -r requirements.txt && pip3 install --no-cache-dir . && \
    cp src/templates/* /etc/rtmon/templates/

# Download CA certificates with a progress bar
WORKDIR /etc/grid-security/certificates/
RUN wget --progress=dot:giga https://raw.githubusercontent.com/sdn-sense/rm-configs/master/CAs/SiteRM.pem -O e52ac827.0

# Copy necessary files
COPY files/etc/supervisord.d/10-server.conf /etc/supervisord.d/10-server.conf
COPY files/etc/supervisord.d/11-httpserver.conf /etc/supervisord.d/11-httpserver.conf
COPY icons/host.png /srv/icons/host.png
COPY icons/switch.png /srv/icons/switch.png
COPY icons/BGP.png /srv/icons/BGP.png

# Get latest CA's while suppressing warnings
RUN fetch-crl || echo "Suppress warnings."
