import socket
import threading
import time

class MeshNode:
    def __init__(self, node_index, nodes):
        self.node_index = node_index
        self.nodes = nodes
        self.host, self.port = self.nodes[self.node_index]
        self.received_weights = {i: None for i in range(len(self.nodes))}
        self._server_socket = None
        self._running = True
        self.server_thread = threading.Thread(
            target=self.server_listen, daemon=True
        )
        self.server_thread.start()
        # Wait a bit to ensure server is up before clients try to connect
        time.sleep(2)

    def server_listen(self):
        """Starts the server to listen for incoming weight data."""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.settimeout(5.0)
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(5)
            print(f"[SERVER] Node {self.node_index} listening on {self.host}:{self.port}")
        except Exception as e:
            print(f"[SERVER ERROR] Node {self.node_index} failed to start server: {e}")
            return

        while self._running:
            try:
                client_conn, _ = self._server_socket.accept()
                client_conn.settimeout(5.0)
                threading.Thread(target=self.handle_connection, args=(client_conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"[SERVER ERROR] Node {self.node_index} accept failed: {e}")

    def handle_connection(self, conn):
        """Handles incoming messages from other nodes."""
        try:
            data = conn.recv(1024)
            if data:
                message = data.decode().strip()
                if message == "TURN GREEN":
                    print(f"[SERVER] Node {self.node_index} received control command: TURN GREEN")
                elif message == "TURN RED":
                    print(f"[SERVER] Node {self.node_index} received control command: TURN RED")
                else:
                    try:
                        tokens = message.split()
                        sender = int(tokens[1])
                        weight_value = float(tokens[4])
                        self.received_weights[sender] = weight_value
                    except (IndexError, ValueError) as e:
                        print(f"[SERVER ERROR] Node {self.node_index} failed to parse weight update: {e}")
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
        for _ in range(max_retries):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5.0)
            try:
                client.connect((target_host, target_port))
                client.sendall(f"Node {self.node_index} detected weight: {weight}".encode())
                break
            except socket.timeout:
                time.sleep(1)
            except Exception:
                time.sleep(1)
            finally:
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
            finally:
                client.close()

    def close(self):
        """Shuts down the server socket and stops the server thread."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass