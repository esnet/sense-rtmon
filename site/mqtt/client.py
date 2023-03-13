import paho.mqtt.client as mqtt
import json

# Define the MQTT broker and topic
broker_address = "dev2.virnao.com"
topic = "example/topic"
port_num = 9091
# Define the file to write the number to
filename = "./exporter_status/node_exporter"

# Define a callback function to handle incoming messages
def on_message(client, userdata, message):
    # Parse the JSON message and extract the string and number values
    message_dict = json.loads(message.payload.decode())
    exporter = message_dict["exporter"]
    status = message_dict["status"]

    # Write the number to the file
    with open(filename, "w") as f:
        f.write(str(status))

# Create an MQTT client instance and set the message callback function
client = mqtt.Client()
client.on_message = on_message

# Connect to the MQTT broker and subscribe to the topic
client.connect(broker_address, port=port_num)
client.subscribe(topic)

# Start the MQTT client loop to listen for incoming messages
client.loop_forever()