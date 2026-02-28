import os
import sys
import time
import asyncio
import socketio
import platform
import tempfile
import subprocess
import socket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import screenshot
import files
import terminal
import rpyc_service
import version

SERVER_URL = os.environ.get('SERVER_URL', 'http://localhost:8000')
CLIENT_ID = os.environ.get('CLIENT_ID', os.environ.get('HOSTNAME', 'client') + '-' + str(os.getpid()))
FPS = 5
FRAME_INTERVAL = 1.0 / FPS
RECONNECT_INTERVAL = int(os.environ.get('RECONNECT_INTERVAL', 1)) * 60
SELF_UPDATE_KILL = os.environ.get('SELF_UPDATE_KILL', 'true').lower() == 'true'

sio = socketio.AsyncClient(reconnection=False)

is_streaming = False

files.setup_file_handlers(sio)
terminal.setup_terminal_handlers(sio)

@sio.event
async def start_streaming():
    global is_streaming
    is_streaming = True
    print(f"DEBUG start_streaming: [{time.time()}] Server requested to start streaming")

@sio.event
async def stop_streaming():
    global is_streaming
    is_streaming = False
    print(f"DEBUG stop_streaming: [{time.time()}] Server requested to stop streaming")

@sio.event
async def connect():
    print(f"DEBUG connect: [{time.time()}] Connected to server, emitting register")
    client_platform = 'windows' if sys.platform == 'win32' else 'linux'
    await sio.emit('register', {
        'client_id': CLIENT_ID,
        'version': version.VERSION,
        'platform': client_platform
    })
    print(f"DEBUG connect: [{time.time()}] Register emitted")

@sio.event
async def connected(data):
    print(f"DEBUG connected: [{time.time()}] Received connected event: {data}")

@sio.event
async def connect_error(data):
    print(f"DEBUG connect_error: [{time.time()}] Connection error: {data}")

@sio.event
async def disconnect():
    global is_streaming
    is_streaming = False
    print(f"DEBUG disconnect: [{time.time()}] Disconnected from server")

@sio.event
async def message(data):
    print(f"DEBUG: Received message: {data}")

@sio.on('get_client_ip')
async def on_get_client_ip(data):
    import socket
    req_id = data.get('req_id')
    webui_sid = data.get('webui_sid')
    
    rpyc_host = os.environ.get('RPYC_HOST')
    if rpyc_host:
        local_ip = rpyc_host
    else:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = '127.0.0.1'
    
    sio.emit('client_ip_response', {
        'ip': local_ip,
        'req_id': req_id,
        'client_id': CLIENT_ID,
        'webui_sid': webui_sid
    })

@sio.on('update_required')
async def on_update_required(data):
    print(f"Update required: {data}")
    
    download_url = data.get('url')
    new_version = data.get('version')
    
    if not download_url:
        print("Update required but no URL provided")
        return
    
    print(f"Downloading update from {download_url}")
    
    try:
        import urllib.request
        
        response = urllib.request.urlopen(download_url)
        binary_data = response.read()
        
        client_platform = 'windows' if sys.platform == 'win32' else 'linux'
        ext = '.exe' if client_platform == 'windows' else ''
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            f.write(binary_data)
            temp_path = f.name
        
        os.chmod(temp_path, 0o755)
        
        print(f"Update downloaded to {temp_path}, executing...")
        
        env = os.environ.copy()
        
        subprocess.run([temp_path], env=env, close_fds=True)
        
        os.unlink(temp_path)
        
        print(f"Update process started, exiting current process (SELF_UPDATE_KILL={SELF_UPDATE_KILL})")
        
        if SELF_UPDATE_KILL:
            sys.exit(0)
        
    except Exception as e:
        print(f"Failed to download/execute update: {e}")
        import traceback
        traceback.print_exc()

async def send_screenshot():
    global is_streaming
    if is_streaming:
        try:
            screenshot_data = screenshot.capture_screenshot()
            await sio.emit('screenshot', {
                'client_id': CLIENT_ID,
                'image': screenshot_data,
                'timestamp': time.time()
            })
            print(f"DEBUG send_screenshot: [{time.time()}] Screenshot sent")
        except Exception as e:
            print(f"Error capturing screenshot: {e}")

async def main():
    global is_streaming
    
    rpyc_service.setup_rpyc_service(CLIENT_ID)
    
    print(f"Remote Debug Client - {CLIENT_ID}")
    print(f"Server: {SERVER_URL}")
    print(f"Target FPS: {FPS}")
    print(f"Reconnect interval: {RECONNECT_INTERVAL // 60} minute(s)")
    print(f"Root directory: {files.ROOT_DIR}")
    print(f"RPyC port: {rpyc_service.RPYC_PORT}")
    
    connected = False
    last_frame_time = 0
    
    while True:
        if not connected:
            try:
                print(f"DEBUG: Attempting to connect...")
                print(f"DEBUG: current time = " + str(time.time()))
                await sio.connect(SERVER_URL, socketio_path='/socket.io', transports=['websocket'])
                print(f"DEBUG: Connect called, sio.connected={sio.connected}")
                connected = True
            except Exception as e:
                print(f"Failed to connect: {e}")
                await asyncio.sleep(RECONNECT_INTERVAL)
                continue
        
        current_time = time.time()
        
        if is_streaming and current_time - last_frame_time >= FRAME_INTERVAL:
            await send_screenshot()
            last_frame_time = current_time
        
        if not sio.connected:
            connected = False
            is_streaming = False
            print(f"DEBUG main: [{time.time()}] Connection lost, sio.connected={sio.connected}")
            await asyncio.sleep(RECONNECT_INTERVAL)
        
        await asyncio.sleep(0.01)

if __name__ == '__main__':
    asyncio.run(main())
