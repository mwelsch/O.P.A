from flask_socketio import SocketIO, emit
from threading import Event
import os
import base64

socketio = None
pending_requests = {}

def setup_file_handlers(socketio_instance, pending_requests_dict):
    global socketio, pending_requests
    socketio = socketio_instance
    pending_requests = pending_requests_dict

    @socketio_instance.on('read_file_response')
    def handle_read_file_response(data):
        req_id = data.pop('req_id', None)
        if req_id and req_id in pending_requests:
            pending_requests[req_id]['event'].set()

    @socketio_instance.on('file_content')
    def handle_file_content(data):
        req_id = data.pop('req_id', None)
        if req_id and req_id in pending_requests:
            pending_requests[req_id]['data'] = data
            pending_requests[req_id]['event'].set()

def get_client_sid(client_id):
    from main import clients
    if client_id in clients:
        return clients[client_id].get('sid')
    return None

def request_file_from_client(client_id, file_path):
    from main import clients
    
    if client_id not in clients:
        return {'error': 'Client not found', 'error_code': 404}
    
    if not clients[client_id].get('connected'):
        return {'error': 'Client not connected', 'error_code': 404}
    
    sid = get_client_sid(client_id)
    if not sid:
        print(f"DEBUG: No SID for client {client_id}")
        return {'error': 'Client SID not found', 'error_code': 500}
    
    print(f"DEBUG: Emitting to sid={sid}, client_id={client_id}")
    
    import uuid
    req_id = str(uuid.uuid4())
    event = Event()
    pending_requests[req_id] = {'data': None, 'event': event}
    
    socketio.emit('read_file', {'path': file_path, 'req_id': req_id}, to=sid)
    
    print(f"DEBUG: Waiting for response...")
    event.wait(timeout=30)
    
    result = pending_requests.pop(req_id, {}).get('data')
    
    if not result:
        print(f"DEBUG: Timeout waiting for client")
        return {'error': 'Timeout waiting for client', 'error_code': 504}
    
    print(f"DEBUG: Got result: {result.get('is_dir')}")
    return result

def setup_file_routes(app, require_auth):
    from flask import jsonify, request, Response
    
    @app.route('/file/<client_id>', methods=['POST'])
    @require_auth
    def view_file(client_id):
        data = request.get_json() or {}
        file_path = data.get('path', '')
        
        result = request_file_from_client(client_id, file_path)
        
        if 'error' in result:
            return jsonify(result), result.get('error_code', 500)
        
        return jsonify(result)

    @app.route('/file/<client_id>/<path:file_path>', methods=['GET'])
    @require_auth
    def view_file_get(client_id, file_path):
        result = request_file_from_client(client_id, file_path)
        
        if 'error' in result:
            return jsonify(result), result.get('error_code', 500)
        
        if result.get('is_dir'):
            return jsonify(result)
        
        content = base64.b64decode(result['content'])
        mime_type = result.get('mime_type', 'text/plain')
        
        if mime_type and mime_type.startswith('text/'):
            return Response(content, content_type=mime_type)
        
        return Response(
            content,
            headers={
                'Content-Type': mime_type or 'application/octet-stream'
            }
        )

    @app.route('/download/<client_id>/<path:file_path>', methods=['GET'])
    @require_auth
    def download_file(client_id, file_path):
        result = request_file_from_client(client_id, file_path)
        
        if 'error' in result:
            return jsonify(result), result.get('error_code', 500)
        
        if result.get('is_dir'):
            return jsonify({'error': 'Cannot download directory'}), 400
        
        content = base64.b64decode(result['content'])
        filename = result.get('filename', os.path.basename(file_path))
        mime_type = result.get('mime_type', 'application/octet-stream')
        
        return Response(
            content,
            headers={
                'Content-Type': mime_type,
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
