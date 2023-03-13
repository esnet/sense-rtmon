import paho.mqtt.client as mqtt
import json

# Define the MQTT broker and topic
broker_address = "localhost"
topic = "example/topic"

# Create an MQTT client instance
client = mqtt.Client()

# Connect to the MQTT broker
client.connect(broker_address)

# Create a message in JSON format
message_dict = {"string_part": "Hello world!", "number_part": 123}
message_json = json.dumps(message_dict)

# Publish the message to the topic
client.publish(topic, message_json)

# Disconnect from the MQTT broker
client.disconnect()