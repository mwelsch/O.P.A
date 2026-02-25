import os
import base64
import mimetypes

ROOT_DIR = os.environ.get('ROOT_DIR', os.path.expanduser('~'))

def handle_read_file(data):
    rel_path = data.get('path', '').lstrip('/')
    full_path = os.path.normpath(os.path.join(ROOT_DIR, rel_path))
    
    if not os.path.exists(full_path):
        print(f"DEBUG: File not found: {full_path}")
        return {'error': 'File not found', 'error_code': 404}
    
    if os.path.isdir(full_path):
        items = []
        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                items.append({
                    'name': item,
                    'is_dir': os.path.isdir(item_path),
                    'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                })
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        except Exception as e:
            return {'error': str(e), 'error_code': 500}
        
        return {
            'path': rel_path,
            'is_dir': True,
            'items': items
        }
    
    try:
        with open(full_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        return {
            'path': rel_path,
            'is_dir': False,
            'content': content,
            'mime_type': mimetypes.guess_type(full_path)[0] or 'application/octet-stream',
            'filename': os.path.basename(full_path)
        }
    except Exception as e:
        return {'error': str(e), 'error_code': 500}

def setup_file_handlers(sio):
    @sio.on('read_file')
    def on_read_file(data):
        print(f"DEBUG: Received read_file event: {data}")
        result = handle_read_file(data)
        req_id = data.get('req_id')
        result['req_id'] = req_id
        print(f"DEBUG: Sending response: is_dir={result.get('is_dir')}")
        sio.emit('file_content', result)
