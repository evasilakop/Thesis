from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress
import time
import node

# === Configuration ===
PORT = "COM06"  # Change to match your serial port
BAUD_RATE = 9600

device = XBeeDevice(PORT, BAUD_RATE)



def decide_green_time(local, neighbor):
    if local > neighbor:
        return 20  # seconds
    else:
        return 3 # to write what happens if the local traffic is not bigger

def main():
    try:
        device.open()
        print("Device opened and running.")

        while True:
            local_traffic = node.weight
            message = f"NODE_A:{local_traffic}"
            print(f"[SEND] {message}")

            device.send_data_broadcast(message)
            time.sleep(1)

            neighbor_traffic = 0
            xbee_message = device.read_data(5)  # 5 sec timeout

            if xbee_message:
                received = xbee_message.data.decode()
                print(f"[RECEIVED] {received}")
                if received.startswith("NODE_B:"):
                    neighbor_traffic = int(received.split(":")[1])

            green_time = decide_green_time(local_traffic, neighbor_traffic)
            print(f"[ACTION] Green light ON for {green_time} seconds\n")

            time.sleep(green_time + 1)

    finally:
        if device is not None and device.is_open():
            device.close()

if __name__ == '__main__':
    main()