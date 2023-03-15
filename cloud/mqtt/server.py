import paho.mqtt.client as mqtt
import json
import time 

# Define the MQTT broker and topic
broker_address = "dev2.virnao.com"
topic = "example/topic"
port_num = 3000

# Create an MQTT client instance
client = mqtt.Client()

# Connect to the MQTT broker
client.connect(broker_address,port=port_num)

# Get the data to send 
def get_date_from_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

example_data = get_date_from_file("node.json")

# Create a message in JSON format
message_dict = example_data
message_json = json.dumps(message_dict)

while True:
    # Publish the message to the topic
    client.publish(topic, message_json)
    print("sending message: " + message_json)
    time.sleep(5)
