import paho.mqtt.client as mqtt
import json
import os
# Define the MQTT broker and topic
broker_address = "dev2.virnao.com"
topic = "example/topic"
port_num = os.getenv("MQTT_PORT")

# Define the file to write the number to
filename = "./received_config.json"

# Define a callback function to handle incoming messages
def on_message(client, userdata, message):
    # Parse the JSON message and extract the string and number values
    message_dict = json.loads(message.payload.decode())
    print(message_dict)
    # Dump json to the file
    with open(filename, "w") as f:
        f.write(json.dumps(message_dict))

# Create an MQTT client instance and set the message callback function
client = mqtt.Client()
client.on_message = on_message

# Connect to the MQTT broker and subscribe to the topic
client.connect(broker_address, port=port_num)
client.subscribe(topic)

# Start the MQTT client loop to listen for incoming messages
client.loop_forever()
