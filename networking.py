import socket
import threading

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

    def server_listen(self):
        """Starts the server to listen for incoming weight data."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"[SERVER] Node {self.node_index} listening "
              f"on {self.host}:{self.port}"
        )

        while True:
            client_conn, addr = server.accept()
            threading.Thread(target=self.handle_connection, 
                             args=(client_conn,), 
                             daemon=True
            ).start()

    def handle_connection(self, conn):
        """Handles incoming messages from other nodes."""
        data = conn.recv(1024)
        if data:
            message = data.decode().strip()
            if message == "TURN GREEN":
                print(f"[SERVER] Node {self.node_index} received "
                      f"control command: TURN GREEN"
                      )
                # code here for turning green
            elif message == "TURN RED":
                print(f"[SERVER] Node {self.node_index} received "
                      f"control command: TURN RED"
                      )
                # code here for turning red
            else:
                # Handle weight updates. Expected format:
                # "Node <sender_index> detected weight: <weight>"
                try:
                    tokens = message.split()
                    sender = int(tokens[1])
                    weight_value = float(tokens[4])
                    self.received_weights[sender] = weight_value
                except (IndexError, ValueError):
                    sender = "Unknown"
                print(
                    f"[SERVER] Node {self.node_index} received "
                    f"weight update from Node {sender}: {message}"
                )
        conn.close()

    def broadcast_weight(self, weight):
        """Sends detected weight to all peer nodes."""
        for idx, (peer_host, peer_port) in enumerate(self.nodes):
            if idx != self.node_index:
                self.send_weight(peer_host, peer_port, weight)

    def send_weight(self, target_host, target_port, weight):
        """Sends data to a specific peer node."""
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((target_host, target_port))
            client.sendall(
                f"Node {self.node_index} detected "
                f"weight: {weight}".encode()
            )
        finally:
            client.close()
    
    def send_control_message(self, target_index, message):
        """
        Sends a control message (like "TURN GREEN" or "TURN RED")
        to the node with the given index.
        """
        target_host, target_port = self.nodes[target_index]
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((target_host, target_port))
            client.sendall(message.encode())
        finally:
            client.close()