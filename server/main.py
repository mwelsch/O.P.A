import os
import base64
import io
from flask import Flask, jsonify, request, Response
from flask_socketio import SocketIO, emit
from PIL import Image
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

clients = {}

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
    with open('/app/web-ui/index.html', 'r') as f:
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
    client_id = request.args.get('client_id')
    if client_id:
        clients[client_id] = {
            'connected': True,
            'screenshot': None,
            'timestamp': None,
            'sid': request.sid
        }
        print(f"Client connected: {client_id}")
        emit('connected', {'client_id': client_id}, broadcast=True)

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

@socketio.on('screenshot')
def handle_screenshot(data):
    client_id = data.get('client_id')
    if client_id and client_id in clients:
        clients[client_id]['screenshot'] = data.get('image')
        clients[client_id]['timestamp'] = data.get('timestamp')
        emit('screenshot_update', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    socketio.run(app, host='0.0.0.0', port=port)
