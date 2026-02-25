#!/usr/bin/env python3
import os
import sys
import time
import socketio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import screenshot
import files

SERVER_URL = os.environ.get('SERVER_URL', 'http://localhost:8000')
CLIENT_ID = os.environ.get('CLIENT_ID', os.environ.get('HOSTNAME', 'client') + '-' + str(os.getpid()))
FPS = 5
FRAME_INTERVAL = 1.0 / FPS
RECONNECT_INTERVAL = int(os.environ.get('RECONNECT_INTERVAL', 1)) * 60

sio = socketio.Client(reconnection=False)

is_streaming = False

files.setup_file_handlers(sio)

@sio.event
def start_streaming():
    global is_streaming
    is_streaming = True
    print(f"DEBUG: Server requested to start streaming")

@sio.event
def stop_streaming():
    global is_streaming
    is_streaming = False
    print(f"DEBUG: Server requested to stop streaming")

@sio.event
def connect():
    print(f"DEBUG: Connected to server, emitting register")
    sio.emit('register', {'client_id': CLIENT_ID})
    print(f"DEBUG: Register emitted")

@sio.event
def connected(data):
    print(f"DEBUG: Received connected event: {data}")

@sio.event
def connect_error(data):
    print(f"DEBUG: Connection error: {data}")

@sio.event
def disconnect():
    global is_streaming
    is_streaming = False
    print(f"DEBUG: Disconnected from server")

@sio.event
def message(data):
    print(f"DEBUG: Received message: {data}")

def main():
    print(f"Remote Debug Client - {CLIENT_ID}")
    print(f"Server: {SERVER_URL}")
    print(f"Target FPS: {FPS}")
    print(f"Reconnect interval: {RECONNECT_INTERVAL // 60} minute(s)")
    print(f"Root directory: {files.ROOT_DIR}")
    
    connected = False
    last_frame_time = 0
    
    while True:
        if not connected:
            try:
                print(f"DEBUG: Attempting to connect...")
                print(f"DEBUG: current time = "+ str(time.time()))
                sio.connect(SERVER_URL, socketio_path='/socket.io')
                print(f"DEBUG: Connect called, sio.connected={sio.connected}")
                connected = True
            except Exception as e:
                print(f"Failed to connect: {e}")
                time.sleep(RECONNECT_INTERVAL)
                continue
        
        current_time = time.time()
        
        if is_streaming and current_time - last_frame_time >= FRAME_INTERVAL:
            try:
                screenshot_data = screenshot.capture_screenshot()
                sio.emit('screenshot', {
                    'client_id': CLIENT_ID,
                    'image': screenshot_data,
                    'timestamp': time.time()
                })
                last_frame_time = current_time
            except Exception as e:
                print(f"Error capturing screenshot: {e}")
        
        if not sio.connected:
            connected = False
            print(f"DEBUG: Connection lost, sio.connected={sio.connected}")
            time.sleep(RECONNECT_INTERVAL)
        
        time.sleep(0.01)

if __name__ == '__main__':
    main()
