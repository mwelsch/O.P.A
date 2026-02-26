from flask import Flask, jsonify, request, Response
from flask_socketio import SocketIO, emit
from functools import wraps
import os
import sys
import threading
import time
import screenshot
import files
import rpyc_server



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
    import time as time_module
    print(f"DEBUG SOCKET: [{time_module.time()}] New socket connected, sid={request.sid}")
    # Check if this is a debug client or web UI
    # Debug clients will emit 'register' event, web UI won't
    print(f"DEBUG SOCKET: [{time_module.time()}] Waiting to see if this is client or web UI...")
    socketio.emit('reload')
    print(f"DEBUG SOCKET: [{time_module.time()}] Sent reload signal to sid={request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    import time as time_module
    client_id = None
    for cid, data in clients.items():
        if data.get('sid') == request.sid:
            client_id = cid
            break
    
    if client_id:
        print(f"DEBUG SOCKET: [{time_module.time()}] Client disconnected: {client_id}, sid={request.sid}")
    else:
        print(f"DEBUG SOCKET: [{time_module.time()}] Socket disconnected (no client_id), sid={request.sid}")
    
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
    import time
    print(f"DEBUG start_viewing: [{time.time()}] Received data={data}")
    print(f"DEBUG start_viewing: [{time.time()}] All clients: {list(clients.keys())}")
    client_id = data.get('client_id')
    print(f"DEBUG start_viewing: [{time.time()}] client_id={client_id}, in clients={client_id in clients}")
    if not client_id or client_id not in clients:
        print(f"DEBUG start_viewing: [{time.time()}] Client not found, returning early")
        return
    
    viewer_sid = request.sid
    
    if client_id not in viewers:
        viewers[client_id] = set()
    
    viewers[client_id].add(viewer_sid)
    
    if len(viewers[client_id]) == 1 and clients[client_id].get('connected'):
        client_sid = clients[client_id].get('sid')
        if client_sid:
            print(f"DEBUG start_viewing: [{time.time()}] Emitting start_streaming to client {client_id}, sid={client_sid}")
            socketio.emit('start_streaming', to=client_sid)
            print(f"DEBUG start_viewing: [{time.time()}] Started streaming for client {client_id}")

@socketio.on('stop_viewing')
def handle_stop_viewing(data):
    print(f"DEBUG stop_viewing: [{time.time()}] Received data={data}")
    client_id = data.get('client_id')
    if not client_id or client_id not in viewers:
        print(f"DEBUG stop_viewing: [{time.time()}] Client not in viewers, returning early")
        return
    
    viewer_sid = request.sid
    viewers[client_id].discard(viewer_sid)
    
    if len(viewers[client_id]) == 0:
        if clients[client_id].get('connected'):
            client_sid = clients[client_id].get('sid')
            if client_sid:
                print(f"DEBUG stop_viewing: [{time.time()}] Emitting stop_streaming to client {client_id}, sid={client_sid}")
                socketio.emit('stop_streaming', to=client_sid)
                print(f"DEBUG stop_viewing: [{time.time()}] Stopped streaming for client {client_id}")

@socketio.on('request_file')
def handle_request_file(data):
    """Handle file request from web UI, forward to target client"""
    import time as time_module
    client_id = data.get('client_id')
    file_path = data.get('path', '')
    request_id = data.get('request_id')
    webui_sid = request.sid
    
    print(f"DEBUG request_file: [{time_module.time()}] Received request for client={client_id}, path={file_path}")
    
    if not client_id or client_id not in clients:
        print(f"DEBUG request_file: [{time_module.time()}] Client {client_id} not found")
        socketio.emit('file_content', {
            'error': 'Client not found',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    if not clients[client_id].get('connected'):
        print(f"DEBUG request_file: [{time_module.time()}] Client {client_id} not connected")
        socketio.emit('file_content', {
            'error': 'Client not connected',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    client_sid = clients[client_id].get('sid')
    if not client_sid:
        print(f"DEBUG request_file: [{time_module.time()}] No SID for client {client_id}")
        socketio.emit('file_content', {
            'error': 'Client SID not found',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    print(f"DEBUG request_file: [{time_module.time()}] Forwarding to client {client_id}, sid={client_sid}")
    socketio.emit('read_file', {
        'path': file_path,
        'req_id': request_id,
        'webui_sid': webui_sid
    }, to=client_sid)

@socketio.on('file_content')
def handle_file_content_from_client(data):
    """Receive file content from client, forward to web UI"""
    import time as time_module
    req_id = data.get('req_id')
    webui_sid = data.pop('webui_sid', None)
    
    print(f"DEBUG file_content: [{time_module.time()}] Received from client, forwarding to web UI")
    
    if webui_sid:
        socketio.emit('file_content', data, to=webui_sid)
    else:
        print(f"DEBUG file_content: [{time_module.time()}] No webui_sid, broadcasting instead")
        socketio.emit('file_content', data)

@socketio.on('execute_command')
def handle_execute_command(data):
    """Handle terminal command from web UI, forward to target client"""
    import time as time_module
    client_id = data.get('client_id')
    command = data.get('command', '')
    shell = data.get('shell')
    detach = data.get('detach', False)
    request_id = data.get('request_id')
    webui_sid = request.sid
    
    print(f"DEBUG execute_command: [{time_module.time()}] Received command for client={client_id}, cmd={command[:50]}...")
    
    if not client_id or client_id not in clients:
        print(f"DEBUG execute_command: [{time_module.time()}] Client {client_id} not found")
        socketio.emit('command_output', {
            'error': 'Client not found',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    if not clients[client_id].get('connected'):
        print(f"DEBUG execute_command: [{time_module.time()}] Client {client_id} not connected")
        socketio.emit('command_output', {
            'error': 'Client not connected',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    client_sid = clients[client_id].get('sid')
    if not client_sid:
        print(f"DEBUG execute_command: [{time_module.time()}] No SID for client {client_id}")
        socketio.emit('command_output', {
            'error': 'Client SID not found',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    print(f"DEBUG execute_command: [{time_module.time()}] Forwarding to client {client_id}, sid={client_sid}, detach={detach}")
    socketio.emit('execute_command', {
        'command': command,
        'shell': shell,
        'detach': detach,
        'req_id': request_id,
        'webui_sid': webui_sid
    }, to=client_sid)
    print(f"DEBUG execute_command: [{time_module.time()}] Emit complete for client {client_id}")

@socketio.on('command_output')
def handle_command_output(data):
    """Receive command output from client, forward to web UI"""
    import time as time_module
    req_id = data.get('req_id')
    webui_sid = data.pop('webui_sid', None)
    
    print(f"DEBUG command_output: [{time_module.time()}] Received from client, forwarding to web UI")
    
    if webui_sid:
        socketio.emit('command_output', data, to=webui_sid)
    else:
        print(f"DEBUG command_output: [{time_module.time()}] No webui_sid")

@socketio.on('get_platform_info')
def handle_get_platform_info(data):
    """Get platform info from client (shell availability)"""
    import time as time_module
    client_id = data.get('client_id')
    webui_sid = request.sid
    
    print(f"DEBUG get_platform_info: [{time_module.time()}] Requesting platform info from client {client_id}")
    
    if not client_id or client_id not in clients:
        print(f"DEBUG get_platform_info: [{time_module.time()}] Client {client_id} not found")
        return
    
    client_sid = clients[client_id].get('sid')
    if client_sid:
        socketio.emit('get_platform_info', {
            'req_id': data.get('req_id'),
            'webui_sid': webui_sid
        }, to=client_sid)

@socketio.on('platform_info')
def handle_platform_info(data):
    """Receive platform info from client, forward to web UI"""
    import time as time_module
    webui_sid = data.pop('webui_sid', None)
    
    print(f"DEBUG platform_info: [{time_module.time()}] Received from client")
    
    if webui_sid:
        socketio.emit('platform_info', data, to=webui_sid)

@socketio.on('detach_command')
def handle_detach_command(data):
    """Handle detach request from web UI, forward to target client"""
    import time as time_module
    client_id = data.get('client_id')
    request_id = data.get('req_id')
    webui_sid = request.sid
    
    print(f"DEBUG detach_command: [{time_module.time()}] Received for client={client_id}, req_id={request_id}")
    
    if not client_id or client_id not in clients:
        print(f"DEBUG detach_command: [{time_module.time()}] Client {client_id} not found")
        socketio.emit('command_output', {
            'error': 'Client not found',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    if not clients[client_id].get('connected'):
        print(f"DEBUG detach_command: [{time_module.time()}] Client {client_id} not connected")
        socketio.emit('command_output', {
            'error': 'Client not connected',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    client_sid = clients[client_id].get('sid')
    if not client_sid:
        print(f"DEBUG detach_command: [{time_module.time()}] No SID for client {client_id}")
        socketio.emit('command_output', {
            'error': 'Client SID not found',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    print(f"DEBUG detach_command: [{time_module.time()}] Forwarding to client {client_id}, sid={client_sid}")
    socketio.emit('detach_command', {
        'req_id': request_id,
        'webui_sid': webui_sid
    }, to=client_sid)

@socketio.on('kill_command')
def handle_kill_command(data):
    """Handle kill request from web UI, forward to target client"""
    import time as time_module
    client_id = data.get('client_id')
    request_id = data.get('req_id')
    webui_sid = request.sid
    
    print(f"DEBUG kill_command: [{time_module.time()}] Received for client={client_id}, req_id={request_id}")
    
    if not client_id or client_id not in clients:
        print(f"DEBUG kill_command: [{time_module.time()}] Client {client_id} not found")
        socketio.emit('command_output', {
            'error': 'Client not found',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    if not clients[client_id].get('connected'):
        print(f"DEBUG kill_command: [{time_module.time()}] Client {client_id} not connected")
        socketio.emit('command_output', {
            'error': 'Client not connected',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    client_sid = clients[client_id].get('sid')
    if not client_sid:
        print(f"DEBUG kill_command: [{time_module.time()}] No SID for client {client_id}")
        socketio.emit('command_output', {
            'error': 'Client SID not found',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    print(f"DEBUG kill_command: [{time_module.time()}] Forwarding to client {client_id}, sid={client_sid}")
    socketio.emit('kill_command', {
        'req_id': request_id,
        'webui_sid': webui_sid
    }, to=client_sid)

@socketio.on('kill_all_commands')
def handle_kill_all_commands(data):
    """Handle kill all commands request from web UI, forward to target client"""
    import time as time_module
    client_id = data.get('client_id')
    webui_sid = request.sid
    
    print(f"DEBUG kill_all_commands: [{time_module.time()}] Received for client={client_id}")
    
    if not client_id or client_id not in clients:
        print(f"DEBUG kill_all_commands: [{time_module.time()}] Client {client_id} not found")
        socketio.emit('command_output', {
            'error': 'Client not found'
        }, to=webui_sid)
        return
    
    if not clients[client_id].get('connected'):
        print(f"DEBUG kill_all_commands: [{time_module.time()}] Client {client_id} not connected")
        socketio.emit('command_output', {
            'error': 'Client not connected'
        }, to=webui_sid)
        return
    
    client_sid = clients[client_id].get('sid')
    if not client_sid:
        print(f"DEBUG kill_all_commands: [{time_module.time()}] No SID for client {client_id}")
        socketio.emit('command_output', {
            'error': 'Client SID not found'
        }, to=webui_sid)
        return
    
    print(f"DEBUG kill_all_commands: [{time_module.time()}] Forwarding to client {client_id}, sid={client_sid}")
    socketio.emit('kill_all_commands', {
        'webui_sid': webui_sid
    }, to=client_sid)

@socketio.on('execute_rpyc_code')
def handle_execute_rpyc_code(data):
    """Execute Python code on client via RPyC"""
    import time as time_module
    client_id = data.get('client_id')
    code = data.get('code', '')
    timeout = data.get('timeout', 60)
    request_id = data.get('request_id')
    webui_sid = request.sid
    
    print(f"DEBUG execute_rpyc_code: [{time_module.time()}] Request for client={client_id}, code={code[:50]}...")
    
    if not client_id:
        socketio.emit('rpyc_output', {
            'error': 'Client ID required',
            'req_id': request_id
        }, to=webui_sid)
        return
    
    result = rpyc_server.execute_code_on_client(client_id, code, timeout)
    result['req_id'] = request_id
    
    if webui_sid:
        result['webui_sid'] = webui_sid
    
    print(f"DEBUG execute_rpyc_code: [{time_module.time()}] Result: success={result.get('success')}")
    socketio.emit('rpyc_output', result, to=webui_sid)

@socketio.on('get_rpyc_status')
def handle_get_rpyc_status(data):
    """Get RPyC connection status for a client"""
    import time as time_module
    client_id = data.get('client_id')
    webui_sid = request.sid
    
    print(f"DEBUG get_rpyc_status: [{time_module.time()}] Request for client={client_id}")
    
    connected = rpyc_server.is_client_connected(client_id)
    result = {
        'connected': connected,
        'client_id': client_id
    }
    
    if connected:
        clients_info = rpyc_server.get_connected_clients()
        if client_id in clients_info:
            result['connected_at'] = clients_info[client_id].get('connected_at')
    
    if webui_sid:
        result['webui_sid'] = webui_sid
    
    socketio.emit('rpyc_session_status', result, to=webui_sid)

@socketio.on('get_system_info')
def handle_get_system_info_via_rpyc(data):
    """Get system info from client via RPyC"""
    import time as time_module
    client_id = data.get('client_id')
    webui_sid = request.sid
    
    print(f"DEBUG get_system_info_rpyc: [{time_module.time()}] Request for client={client_id}")
    
    if not client_id:
        socketio.emit('rpyc_output', {
            'error': 'Client ID required'
        }, to=webui_sid)
        return
    
    result = rpyc_server.get_client_system_info(client_id)
    
    if webui_sid:
        result['webui_sid'] = webui_sid
    
    socketio.emit('rpyc_output', result, to=webui_sid)

screenshot.setup_screenshot_handlers(socketio, clients)

files.setup_file_handlers(socketio, clients, pending_requests)
files.setup_file_routes(app, require_auth)

if __name__ == '__main__':
    rpyc_server.setup_rpyc_server()
    
    port = int(os.environ.get('PORT', 8000))
    socketio.run(app, host='0.0.0.0', port=port)
