#!/usr/bin/env python3
import os
import sys
import time
import base64
import io
import json
import mss
import socketio

SERVER_URL = os.environ.get('SERVER_URL', 'http://localhost:8000')
CLIENT_ID = os.environ.get('CLIENT_ID', os.environ.get('HOSTNAME', 'client') + '-' + str(os.getpid()))
FPS = 5
FRAME_INTERVAL = 1.0 / FPS

sio = socketio.Client(reconnection=True, reconnection_attempts=0)

def capture_screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=70)
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"

@sio.event
def connect():
    print(f"Connected to server as {CLIENT_ID}")
    sio.emit('connect', {'client_id': CLIENT_ID})

@sio.event
def connect_error(data):
    print(f"Connection error: {data}")

@sio.event
def disconnect():
    print("Disconnected from server")

def main():
    print(f"Remote Debug Client - {CLIENT_ID}")
    print(f"Server: {SERVER_URL}")
    print(f"Target FPS: {FPS}")
    
    try:
        sio.connect(SERVER_URL, socketio_path='/socket.io')
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)
    
    last_frame_time = 0
    
    while True:
        current_time = time.time()
        
        if current_time - last_frame_time >= FRAME_INTERVAL:
            try:
                screenshot = capture_screenshot()
                sio.emit('screenshot', {
                    'client_id': CLIENT_ID,
                    'image': screenshot,
                    'timestamp': time.time()
                })
                last_frame_time = current_time
            except Exception as e:
                print(f"Error capturing screenshot: {e}")
        
        time.sleep(0.01)

if __name__ == '__main__':
    main()
