import socket
import threading
import time

class MeshNode:
    def __init__(self, node_index, nodes):
        self.node_index = node_index
        self.nodes = nodes
        self.host, self.port = self.nodes[self.node_index]
        self.received_weights = {i: None for i in range(len(self.nodes))}

        self.server_thread = threading.Thread(
            target=self.server_listen, daemon=True
        )
        self.server_thread.start()
        # Wait a bit to ensure server is up before clients try to connect
        time.sleep(2)

    def server_listen(self):
        """Starts the server to listen for incoming weight data."""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.settimeout(5.0)  # Set server socket timeout to 5 seconds
            server.bind((self.host, self.port))
            server.listen(5)
            print(f"[SERVER] Node {self.node_index} listening "
                  f"on {self.host}:{self.port}")
        except Exception as e:
            print(f"[SERVER ERROR] Node {self.node_index} failed to start server: {e}")
            return

        while True:
            try:
                client_conn, addr = server.accept()
                client_conn.settimeout(5.0)  # Set timeout for client connection
                # print(f"[SERVER] Node {self.node_index} accepted connection from {addr}")
                threading.Thread(target=self.handle_connection, 
                                 args=(client_conn,), 
                                 daemon=True
                ).start()
            except socket.timeout:
                continue  # Accept again after timeout
            except Exception as e:
                print(f"[SERVER ERROR] Node {self.node_index} accept failed: {e}")

    def handle_connection(self, conn):
        """Handles incoming messages from other nodes."""
        try:
            data = conn.recv(1024)
            # print(f"[SERVER] Node {self.node_index} received raw data: {data}")
            if data:
                message = data.decode().strip()
                # print(f"[SERVER] Node {self.node_index} received message: {message}")
                if message == "TURN GREEN":
                    print(f"[SERVER] Node {self.node_index} received "
                          f"control command: TURN GREEN")
                    # code here for turning green
                elif message == "TURN RED":
                    print(f"[SERVER] Node {self.node_index} received "
                          f"control command: TURN RED")
                    # code here for turning red
                else:
                    # Handle weight updates. Expected format:
                    # "Node <sender_index> detected weight: <weight>"
                    try:
                        tokens = message.split()
                        sender = int(tokens[1])
                        weight_value = float(tokens[4])
                        self.received_weights[sender] = weight_value
                    except (IndexError, ValueError) as e:
                        sender = "Unknown"
                        print(f"[SERVER ERROR] Node {self.node_index} failed to parse weight update: {e}")
                    #print(
                    #    f"[SERVER] Node {self.node_index} received "
                    #    f"weight update from Node {sender}: {message}"
                    #)
        except socket.timeout:
            print(f"[SERVER ERROR] Node {self.node_index} connection timed out.")
        except Exception as e:
            print(f"[SERVER ERROR] Node {self.node_index} handle_connection exception: {e}")
        finally:
            conn.close()

    def broadcast_weight(self, weight):
        """Sends detected weight to all peer nodes."""
        for idx, (peer_host, peer_port) in enumerate(self.nodes):
            if idx != self.node_index:
                self.send_weight(peer_host, peer_port, weight)

    def send_weight(self, target_host, target_port, weight):
        """Sends data to a specific peer node."""
        max_retries = 5
        for attempt in range(max_retries):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5.0)  # Set client socket timeout to 5 seconds
            try:
            #    print(f"[CLIENT] Node {self.node_index} attempting to send weight to {target_host}:{target_port} (attempt {attempt+1})")
                client.connect((target_host, target_port))
                client.sendall(
                    f"Node {self.node_index} detected "
                    f"weight: {weight}".encode()
                )
            #    print(f"[CLIENT] Node {self.node_index} sent weight to {target_host}:{target_port}")
                break
            except socket.timeout:
            #    print(f"[CLIENT ERROR] Node {self.node_index} send_weight to {target_host}:{target_port} timed out (attempt {attempt+1})")
                time.sleep(1)
            except Exception as e:
            #    print(f"[CLIENT ERROR] Node {self.node_index} send_weight to {target_host}:{target_port} failed: {e} (attempt {attempt+1})")
                time.sleep(1)
            finally:
                client.close()
    
    def send_control_message(self, target_index, message):
        """
        Sends a control message (like "TURN GREEN" or "TURN RED")
        to the node with the given index.
        """
        target_host, target_port = self.nodes[target_index]
        max_retries = 5
        for attempt in range(max_retries):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5.0)  # Set client socket timeout to 5 seconds
            try:
            #    print(f"[CLIENT] Node {self.node_index} attempting to send control message to {target_host}:{target_port} (attempt {attempt+1})")
                client.connect((target_host, target_port))
                client.sendall(message.encode())
            #    print(f"[CLIENT] Node {self.node_index} sent control message to {target_host}:{target_port}")
                break
            except socket.timeout:
            #    print(f"[CLIENT ERROR] Node {self.node_index} send_control_message to {target_host}:{target_port} timed out (attempt {attempt+1})")
                time.sleep(1)
            except Exception as e:
            #    print(f"[CLIENT ERROR] Node {self.node_index} send_control_message to {target_host}:{target_port} failed: {e} (attempt {attempt+1})")
                time.sleep(1)
            finally:
                client.close()