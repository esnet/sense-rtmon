FROM eclipse-mosquitto

RUN apt-get update && apt-get install -y python3 python3-pip

COPY mqtt_client.py /mqtt_client.py
RUN chmod +x /mqtt_client.py

# CMD ["/usr/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"] 

ENTRYPOINT [ "/home/run.sh" ]