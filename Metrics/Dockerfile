FROM python:3

ADD TCPMetrics /

RUN pip install prometheus_client
RUN pip install pyyaml
RUN apt update -y && apt install tcpdump -y

CMD [ "python3", "hostMetrics.py", "hostMetricConfig.yml", "&", "(", "sleep", "1", "&&", "python3", "json_exporter_tcp.py", "hostMetricConfig.yml", ")" ]
