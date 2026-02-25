from flask_socketio import SocketIO, emit
import time

socketio = None
clients = {}

def setup_screenshot_handlers(socketio_instance, clients_dict):
    global socketio, clients
    socketio = socketio_instance
    clients = clients_dict
    
    @socketio.on('screenshot')
    def handle_screenshot(data):
        client_id = data.get('client_id')
        print(f"DEBUG screenshot: [{time.time()}] Received screenshot from {client_id}")
        if client_id and client_id in clients:
            clients[client_id]['screenshot'] = data.get('image')
            clients[client_id]['timestamp'] = data.get('timestamp')
            emit('screenshot_update', data, broadcast=True)
            print(f"DEBUG screenshot: [{time.time()}] Broadcasted screenshot for {client_id}")

def get_latest_screenshot(client_id):
    if client_id not in clients:
        return None
    
    return {
        'screenshot': clients[client_id].get('screenshot'),
        'timestamp': clients[client_id].get('timestamp', '')
    }
