from flask import Flask, jsonify, request, Response
from flask_socketio import SocketIO, emit
from functools import wraps
import os
import sys
import threading
import time
import screenshot
import files



sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

clients = {}
pending_requests = {}
viewers = {}
CLIENT_TIMEOUT = 60
removal_timers = {}

def remove_client(client_id):
    if client_id in clients:
        del clients[client_id]
    if client_id in viewers:
        del viewers[client_id]
    if client_id in removal_timers:
        del removal_timers[client_id]
    socketio.emit('client_removed', {'client_id': client_id})
    print(f"Client removed: {client_id}")

def schedule_client_removal(client_id):
    if client_id in removal_timers:
        removal_timers[client_id].cancel()
    
    timer = threading.Timer(CLIENT_TIMEOUT, remove_client, args=[client_id])
    removal_timers[client_id] = timer
    timer.start()
    print(f"Scheduled removal of client {client_id} in {CLIENT_TIMEOUT} seconds")

def cancel_client_removal(client_id):
    if client_id in removal_timers:
        removal_timers[client_id].cancel()
        del removal_timers[client_id]
        print(f"Cancelled removal of client {client_id}")

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin123')

def check_auth():
    auth = request.authorization
    return auth and auth.username == ADMIN_USER and auth.password == ADMIN_PASS

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth():
            return Response('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Remote Debug"'})
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@require_auth
def index():
    web_ui_path = '/app/web-ui/index.html'
    if not os.path.exists(web_ui_path):
        web_ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web-ui', 'index.html')
    with open(web_ui_path, 'r') as f:
        return f.read()

@app.route('/clients')
@require_auth
def list_clients():
    return jsonify([
        {
            'id': client_id,
            'connected': data.get('connected', False)
        }
        for client_id, data in clients.items()
    ])

@app.route('/clients/<client_id>/latest')
@require_auth
def get_latest_screenshot(client_id):
    if client_id not in clients:
        return jsonify({'error': 'Client not found'}), 404
    
    screenshot_data = clients[client_id].get('screenshot')
    if not screenshot_data:
        return jsonify({'error': 'No screenshot available'}), 404
    
    return jsonify({
        'screenshot': screenshot_data,
        'timestamp': clients[client_id].get('timestamp', '')
    })

@socketio.on('connect')
def handle_connect():
    print(f"DEBUG: Socket connect received, sid={request.sid}")
    socketio.emit('reload')
    print(f"DEBUG: Sent reload signal to client")

@socketio.on('disconnect')
def handle_disconnect():
    client_id = None
    for cid, data in clients.items():
        if data.get('sid') == request.sid:
            client_id = cid
            break
    
    if client_id:
        clients[client_id]['connected'] = False
        print(f"Client disconnected: {client_id}")
        emit('disconnected', {'client_id': client_id}, broadcast=True)
        schedule_client_removal(client_id)

@socketio.on('register')
def handle_client_connect(data):
    print(f"DEBUG: Received register event: {data}")
    client_id = data.get('client_id')
    if client_id:
        cancel_client_removal(client_id)
        clients[client_id] = {
            'connected': True,
            'screenshot': None,
            'timestamp': None,
            'sid': request.sid
        }
        print(f"Client registered: {client_id} with sid={request.sid}")
        print(f"DEBUG: Clients dict now: {clients}")
        emit('connected', {'client_id': client_id}, broadcast=True)

@socketio.on('start_viewing')
def handle_start_viewing(data):
    client_id = data.get('client_id')
    if not client_id or client_id not in clients:
        return
    
    viewer_sid = request.sid
    
    if client_id not in viewers:
        viewers[client_id] = set()
    
    viewers[client_id].add(viewer_sid)
    
    if len(viewers[client_id]) == 1 and clients[client_id].get('connected'):
        client_sid = clients[client_id].get('sid')
        if client_sid:
            socketio.emit('start_streaming', to=client_sid)
            print(f"DEBUG: Started streaming for client {client_id}")

@socketio.on('stop_viewing')
def handle_stop_viewing(data):
    client_id = data.get('client_id')
    if not client_id or client_id not in viewers:
        return
    
    viewer_sid = request.sid
    viewers[client_id].discard(viewer_sid)
    
    if len(viewers[client_id]) == 0:
        if clients[client_id].get('connected'):
            client_sid = clients[client_id].get('sid')
            if client_sid:
                socketio.emit('stop_streaming', to=client_sid)
                print(f"DEBUG: Stopped streaming for client {client_id}")

screenshot.setup_screenshot_handlers(socketio, clients)

files.setup_file_handlers(socketio, pending_requests)
files.setup_file_routes(app, require_auth)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    socketio.run(app, host='0.0.0.0', port=port)
