import paho.mqtt.client as mqtt
import json

# Define the MQTT broker and topic
broker_address = "http://dev2.virnao.com"
topic = "example/topic"

# Create an MQTT client instance
client = mqtt.Client()

# Connect to the MQTT broker
client.connect(broker_address,port=3000)

# Create a message in JSON format
message_dict = {"exporter": "node", "status": 1}
message_json = json.dumps(message_dict)

# Publish the message to the topic
client.publish(topic, message_json)

# Disconnect from the MQTT broker
client.disconnect()