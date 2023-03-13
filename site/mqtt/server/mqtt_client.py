import paho.mqtt.client as mqtt
import os

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/example/request")

def on_message(client, userdata, msg):
    print("Message received: " + str(msg.payload))
    if msg.payload == b"node_exporter_on":
        with open("./exporter_status/node_exporter", "w") as file:
            file.write("1")
    if msg.payload == b"node_exporter_off":
        with open("./exporter_status/node_exporter", "w") as file:
            file.write("0")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.loop_forever()