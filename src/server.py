import socket
import threading
import json
import time
from datetime import datetime

PORT = 12345

class AlertServer:
    def __init__(self):
        self.clients = {}  # {client_id: {'socket': socket, 'address': address, 'username': username}}
        self.client_counter = 0
        self.server_socket = None
        
    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', PORT))
        self.server_socket.listen(5)  # Allow up to 5 pending connections
        
        print(f"[{self.get_timestamp()}] Server started on port {PORT}")
        print(f"[{self.get_timestamp()}] Waiting for clients to connect...")
        
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                self.client_counter += 1
                client_id = self.client_counter
                
                # Store client info
                self.clients[client_id] = {
                    'socket': client_socket,
                    'address': client_address,
                    'username': f"Client_{client_id}"
                }
                
                print(f"[{self.get_timestamp()}] New client connected: {client_address} (ID: {client_id})")
                print(f"[{self.get_timestamp()}] Total clients: {len(self.clients)}")
                
                # Start a thread to handle this client
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_id,),
                    daemon=True
                )
                client_thread.start()
                
                # Send welcome message and client list
                self.send_client_list_update()
                
        except KeyboardInterrupt:
            print(f"\n[{self.get_timestamp()}] Server shutting down...")
            self.shutdown()
        except Exception as e:
            print(f"[{self.get_timestamp()}] Server error: {e}")
            self.shutdown()
    
    def handle_client(self, client_id):
        client_info = self.clients[client_id]
        client_socket = client_info['socket']
        client_address = client_info['address']
        
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                print(f"[{self.get_timestamp()}] Received from {client_address} (ID: {client_id}): {data}")
                
                # Parse the message
                try:
                    message_data = json.loads(data)
                    self.process_message(client_id, message_data)
                except json.JSONDecodeError:
                    # Handle legacy string messages (STOP, COLD, etc.)
                    self.process_legacy_message(client_id, data)
                    
        except ConnectionResetError:
            print(f"[{self.get_timestamp()}] Client {client_address} (ID: {client_id}) disconnected abruptly")
        except Exception as e:
            print(f"[{self.get_timestamp()}] Error handling client {client_id}: {e}")
        finally:
            self.disconnect_client(client_id)
    
    def process_message(self, sender_id, message_data):
        message_type = message_data.get('type')
        target_id = message_data.get('target_id')
        
        if message_type == 'CUSTOM':
            # Custom alert message
            self.broadcast_alert(sender_id, message_data, target_id)
        elif message_type == 'CLIENT_LIST_REQUEST':
            # Send client list to requesting client
            self.send_client_list(sender_id)
        elif message_type == 'SET_USERNAME':
            # Update client username
            new_username = message_data.get('username', f"Client_{sender_id}")
            self.clients[sender_id]['username'] = new_username
            print(f"[{self.get_timestamp()}] Client {sender_id} changed username to: {new_username}")
            self.send_client_list_update()
        else:
            print(f"[{self.get_timestamp()}] Unknown message type: {message_type}")
    
    def process_legacy_message(self, sender_id, alert_type):
        # Handle legacy string alerts (STOP, COLD, ALERT1, etc.)
        message_data = {
            'type': 'LEGACY_ALERT',
            'alert_type': alert_type,
            'sender_id': sender_id,
            'sender_username': self.clients[sender_id]['username']
        }
        self.broadcast_alert(sender_id, message_data)
    
    def broadcast_alert(self, sender_id, message_data, target_id=None):
        sender_username = self.clients[sender_id]['username']
        message_data['sender_id'] = sender_id
        message_data['sender_username'] = sender_username
        
        if target_id and target_id in self.clients:
            # Send to specific client
            self.send_to_client(target_id, message_data)
            print(f"[{self.get_timestamp()}] Alert sent from {sender_username} to Client {target_id}")
        else:
            # Broadcast to all other clients
            recipients = 0
            for client_id, client_info in self.clients.items():
                if client_id != sender_id:  # Don't send back to sender
                    if self.send_to_client(client_id, message_data):
                        recipients += 1
            
            print(f"[{self.get_timestamp()}] Alert from {sender_username} broadcasted to {recipients} clients")
    
    def send_to_client(self, client_id, data):
        try:
            client_socket = self.clients[client_id]['socket']
            message = json.dumps(data)
            client_socket.send(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"[{self.get_timestamp()}] Failed to send to client {client_id}: {e}")
            # Client might be disconnected, remove it
            if client_id in self.clients:
                self.disconnect_client(client_id)
            return False
    
    def send_client_list(self, client_id):
        client_list = []
        for cid, info in self.clients.items():
            if cid != client_id:  # Don't include requesting client
                client_list.append({
                    'id': cid,
                    'username': info['username'],
                    'address': str(info['address'])
                })
        
        response = {
            'type': 'CLIENT_LIST_RESPONSE',
            'clients': client_list
        }
        self.send_to_client(client_id, response)
    
    def send_client_list_update(self):
        # Send updated client list to all clients
        for client_id in list(self.clients.keys()):
            self.send_client_list(client_id)
    
    def disconnect_client(self, client_id):
        if client_id in self.clients:
            client_info = self.clients[client_id]
            try:
                client_info['socket'].close()
            except:
                pass
            
            print(f"[{self.get_timestamp()}] Client {client_info['address']} (ID: {client_id}) disconnected")
            del self.clients[client_id]
            print(f"[{self.get_timestamp()}] Total clients: {len(self.clients)}")
            
            # Update client list for remaining clients
            if self.clients:
                self.send_client_list_update()
    
    def get_timestamp(self):
        return datetime.now().strftime("%H:%M:%S")
    
    def shutdown(self):
        print(f"[{self.get_timestamp()}] Closing all client connections...")
        for client_id in list(self.clients.keys()):
            self.disconnect_client(client_id)
        
        if self.server_socket:
            self.server_socket.close()
        print(f"[{self.get_timestamp()}] Server shutdown complete")

if __name__ == "__main__":
    server = AlertServer()
    server.start_server()