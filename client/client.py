#!/usr/bin/env python3
import os
import sys
import time
import asyncio
import socketio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import screenshot
import files

SERVER_URL = os.environ.get('SERVER_URL', 'http://localhost:8000')
CLIENT_ID = os.environ.get('CLIENT_ID', os.environ.get('HOSTNAME', 'client') + '-' + str(os.getpid()))
FPS = 5
FRAME_INTERVAL = 1.0 / FPS
RECONNECT_INTERVAL = int(os.environ.get('RECONNECT_INTERVAL', 1)) * 60

sio = socketio.AsyncClient(reconnection=False)

is_streaming = False

files.setup_file_handlers(sio)

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
    await sio.emit('register', {'client_id': CLIENT_ID})
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