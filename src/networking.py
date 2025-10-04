import socket
import threading
import time

class MeshNode:
    def __init__(self, node_index, nodes, sumo=None):
        self.node_index = node_index
        self.nodes = nodes
        self.host, self.port = self.nodes[self.node_index]
        self.received_weights = {i: None for i in range(len(self.nodes))}
        self._server_socket = None
        self._running = True
        self.sumo = sumo
        self.server_thread = threading.Thread(
            target=self.server_listen, daemon=True
        )
        self.server_thread.start()
        # Wait a bit to ensure server is up before clients try to connect
        time.sleep(2)

    def server_listen(self):
        """Starts the server to listen for incoming data."""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.settimeout(3.0)
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(3)
            print(f"[SERVER] Node {self.node_index} listening on {self.host}:{self.port}")
        except Exception as e:
            print(f"[SERVER ERROR] Node {self.node_index} failed to start server: {e}")
            return

        while self._running:
            try:
                client_conn, _ = self._server_socket.accept()
                client_conn.settimeout(3.0)
                threading.Thread(target=self.handle_connection, args=(client_conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"[SERVER ERROR] Node {self.node_index} accept failed: {e}")

    def handle_connection(self, conn):
        """Handles incoming connections from other nodes.
        """
        try:
            data = conn.recv(1024)
            if data:
                message = data.decode().strip()
                if message == "TURN GREEN":
                    print(f"[SERVER] Node {self.node_index} received control command: TURN GREEN")
                elif message == "TURN RED":
                    print(f"[SERVER] Node {self.node_index} received control command: TURN RED")
                elif message.startswith("Node") and "detected weight:" in message:
                    try:
                        tokens = message.split()
                        sender = int(tokens[1])
                        weight_value = float(tokens[4])
                        self.received_weights[sender] = weight_value
                    except (IndexError, ValueError) as e:
                        print(f"[SERVER ERROR] Node {self.node_index} failed to parse weight update: {e}")
                elif "Vehicle data from node" in message:
                    try:
                        data_part = message.split(":", 1)[1].strip()
                        vehicle_fields = [field.strip() for field in data_part.split(",")]
                        vehicle_id = vehicle_fields[0]
                        route_id = vehicle_fields[1]
                        edge_from = vehicle_fields[2]
                        edge_to = vehicle_fields[3]
                        depart_counter = int(vehicle_fields[4])
                        vehicle_type = vehicle_fields[5]
                        if self.sumo is not None:
                            self.sumo.add_vehicle(vehicle_id, route_id,
                                                  edge_from, edge_to, 
                                                  depart_time=depart_counter, 
                                                  vtype=vehicle_type)
                        else:
                            print(f"[SERVER WARNING] SumoController not set for Node {self.node_index},"
                                  f" cannot add vehicle.")
                    except Exception as e:
                        print(f"[SERVER ERROR] Node {self.node_index} failed to parse vehicle data: {e}")
                else: 
                    print(f"[SERVER WARNING] Node {self.node_index} received unknown message: {message}")
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
        max_retries = 3
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3.0)
        for _ in range(max_retries):
            try:
                client.connect((target_host, target_port))
                client.sendall(f"Node {self.node_index} detected weight: {weight}".encode())
                break
            except socket.timeout:
                time.sleep(1)
            except Exception:
                time.sleep(1)
        client.close()
    
    def send_control_message(self, target_index, message):
        """Sends a control message ('TURN GREEN' or 'TURN RED') to the node with the given index."""
        target_host, target_port = self.nodes[target_index]
        max_retries = 5
        for _ in range(max_retries):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5.0)
            try:
                client.connect((target_host, target_port))
                client.sendall(message.encode())
                break
            except socket.timeout:
                time.sleep(1)
            except Exception:
                time.sleep(1)
        client.close()

    def close(self):
        """Shuts down the server socket and stops the server thread."""
        self._running = False
        if self._server_socket:
            self._server_socket.close()

    def broadcast_message(self, message):
        """Sends detected weight to all peer nodes."""
        for idx, (peer_host, peer_port) in enumerate(self.nodes):
            if idx != self.node_index:
                self.send_message(peer_host, peer_port, message)

    def send_message(self, target_host, target_port, message):
        """Sends data to a specific peer node."""
        max_retries = 3
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3.0)
        for _ in range(max_retries):
            try:
                client.connect((target_host, target_port))
                client.sendall(f"Message from node {self.node_index} : {message}".encode())
                break
            except socket.timeout:
                time.sleep(1)
            except Exception:
                time.sleep(1)
        client.close()