FROM python:3

ADD TCPMetrics /

RUN pip install prometheus_client
RUN pip install pyyaml
RUN pip install requests
RUN apt update -y && apt install tcpdump -y

CMD ["bash", "tcpMetrics.sh"]
