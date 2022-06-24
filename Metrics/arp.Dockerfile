FROM python:3

ADD ARPMetrics /

RUN pip install prometheus_client
RUN pip install pyyaml
RUN pip install requests
RUN apt update -y && apt install tcpdump -y

CMD ["bash", "arpMetrics.sh"]
