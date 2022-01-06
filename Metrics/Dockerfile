FROM python:3

ADD json_exporter.py /

RUN pip install prometheus_client

CMD [ "python", "./json_exporter.py", "9191", "data.json" ]