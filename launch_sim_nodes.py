import serial
import serial.tools.list_ports
from multiprocessing import Process
import time

BAUD_RATE = 9600

def is_port_available(port_name):
    try:
        with serial.Serial(port=port_name, baudrate=BAUD_RATE,
                           timeout=1) as ser:
            ser.write(b"ping\n")
        return True
    except serial.SerialException:
        return False

def find_working_ports():
    ports = serial.tools.list_ports.comports()
    working_ports = []
    target_ports = [6, 8]  # COM6 and COM8 are the "talker" ends

    for p in ports:
        port_name = p.device
        try:
            if port_name.startswith("COM"):
                port_num = int(port_name[3:])
            elif port_name.startswith("/dev/ttyUSB"):
                port_num = int(port_name.replace("/dev/ttyUSB", ""))
            else:
                continue

            if port_num in target_ports and is_port_available(port_name):
                working_ports.append(port_name)
        except ValueError:
            continue

    return working_ports

def run_node(port, node_id):
    import serial
    import threading
    from node import WeightDetector

    video_path = "video.mp4"
    detector = WeightDetector(video_path)
    def listener(ser):
        while True:
            try:
                line = ser.readline().decode(errors='ignore').strip()
                if line:
                    print(f"[{node_id}] Received: {line}")
            except serial.SerialException:
                break

    def sender(ser):
        while True:
            try:
                for weight in detector:
                    message = f"{node_id} weight={weight}"
                    ser.write((message + '\n').encode())
                    print(f"[{node_id}] Sent: {message}")
            except serial.SerialException:
                break

    print(f"[{node_id}] Starting on {port}")
    with serial.Serial(port, BAUD_RATE, timeout=1) as ser:
        threading.Thread(target=listener, args=(ser,), daemon=True).start()
        sender(ser)  # blocks

def launch_nodes(num_nodes):
    ports = find_working_ports()
    if len(ports) < num_nodes:
        print(f"Not enough available ports. Needed: {num_nodes}, Found: {len(ports)}")
        return

    processes = []
    for i in range(num_nodes):
        node_id = f"Node{i}"
        p = Process(target=run_node, args=(ports[i], node_id))
        p.start()
        processes.append(p)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down nodes...")
        for p in processes:
            p.terminate()
            p.join()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=
            "Launch simulated XBee nodes on available COM ports.")
    parser.add_argument("--nodes", type=int, default=2, 
                        help="Number of nodes to launch")
    args = parser.parse_args()

    print(f"Launching {args.nodes} simulated nodes...")
    launch_nodes(args.nodes)