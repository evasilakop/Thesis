import time
import sys

from paho.mqtt import client as mqtt_client


#broker = 
#port = 1883 #default for mqtt
topic = "weights"
# Generate a Client ID with the publish prefix.
#client_id = 

def connect_mqtt():
    #callback function, gets called after the client gets a message from the broker
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id,
                                protocol = mqtt_client.MQTTv5)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    while True:
        time.sleep(1)
        # msg = whatever weight we get back
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")


def run():
    client = connect_mqtt()
    publish(client)
    client.loop_forever()


if __name__ == '__main__':
    run()