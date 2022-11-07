FROM python:3

ADD ARPMetrics /

RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install prometheus_client
RUN pip install pyyaml
RUN pip install requests
RUN apt update -y && apt install tcpdump -y

CMD ["bash", "arpMetrics.sh"]
