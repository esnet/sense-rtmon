import paho.mqtt.client as mqtt
import json

# Define the MQTT broker and topic
broker_address = "172.31.72.189"
topic = "example/topic"
port_num = 3000

# Create an MQTT client instance
client = mqtt.Client()

# Connect to the MQTT broker
client.connect(broker_address,port=port_num)

# Create a message in JSON format
message_dict = {"exporter": "node", "status": 1}
message_json = json.dumps(message_dict)
print("sending message: " + message_json)
# Publish the message to the topic
client.publish(topic, message_json)

# Disconnect from the MQTT broker
# client.disconnect()