import os
import sys
import rpyc
import threading
import time


RPYC_SERVER = os.environ.get('RPYC_SERVER', '')
RPYC_PORT = int(os.environ.get('RPYC_PORT', 28946))
RPYC_SECRET = os.environ.get('RPYC_SECRET', 'ChangeThisSecret')


class ReverseConnection:
    def __init__(self, client_id):
        self.client_id = client_id
        self.conn = None
        self.connected = False
        self.reconnect_interval = 10
        self.running = False
        self._thread = None
    
    def connect(self):
        if not RPYC_SERVER:
            print(f"RPyC: RPYC_SERVER not set, skipping reverse connection")
            return False
        
        try:
            host = RPYC_SERVER
            port = RPYC_PORT
            
            print(f"RPyC: Connecting to {host}:{port}")
            
            self.conn = rpyc.connect(host, port, config={
                'allow_public_attrs': True,
                'allow_getattr': True,
                'allow_all_attrs': True,
                'sync_timeout': 30,
                'async_timeout': 30
            })
            
            result = self.conn.root.register(self.client_id, RPYC_SECRET)
            
            if result[0]:
                self.connected = True
                print(f"RPyC: Successfully registered with server as '{self.client_id}'")
                return True
            else:
                print(f"RPyC: Registration failed: {result[1]}")
                self.conn.close()
                self.conn = None
                return False
                
        except Exception as e:
            print(f"RPyC: Failed to connect: {e}")
            self.conn = None
            return False
    
    def disconnect(self):
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
            self.connected = False
    
    def execute_code(self, code, timeout=60):
        if not self.connected or not self.conn:
            return {'success': False, 'error': 'Not connected to server'}
        
        try:
            result = self.conn.root.execute_code(code, timeout=timeout)
            success, res, output, error, timestamp = result
            return {
                'success': success,
                'result': res,
                'output': output,
                'error': error,
                'timestamp': timestamp
            }
        except Exception as e:
            print(f"RPyC: Error executing code: {e}")
            self.connected = False
            return {'success': False, 'error': str(e)}
    
    def get_system_info(self):
        if not self.connected or not self.conn:
            return {'error': 'Not connected to server'}
        
        try:
            client_id, info = self.conn.root.get_system_info()
            info['client_id'] = client_id
            return info
        except Exception as e:
            print(f"RPyC: Error getting system info: {e}")
            self.connected = False
            return {'error': str(e)}
    
    def _run(self):
        while self.running:
            if not self.connected:
                success = self.connect()
                if not success:
                    time.sleep(self.reconnect_interval)
            else:
                time.sleep(5)
    
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"RPyC: Reverse connection started")
    
    def stop(self):
        self.disconnect()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None


_reverse_connection = None


def setup_reverse_connection(client_id):
    global _reverse_connection
    
    _reverse_connection = ReverseConnection(client_id)
    _reverse_connection.start()
    
    return _reverse_connection


def get_reverse_connection():
    return _reverse_connection


def stop_reverse_connection():
    global _reverse_connection
    
    if _reverse_connection:
        _reverse_connection.stop()
        _reverse_connection = None
