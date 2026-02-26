import os
import sys
import rpyc
from rpyc import Service
import threading
import time
import socket


RPYC_PORT = int(os.environ.get('RPYC_PORT', 28946))
RPYC_SECRET = os.environ.get('RPYC_SECRET', 'ChangeThisSecret')


_connected_clients = {}
_clients_lock = threading.Lock()


class ClientRegistryService(Service):
    _rpyc_config = {
        'allow_public_attrs': True,
        'allow_getattr': True,
        'allow_all_attrs': True,
    }
    
    def exposed_register(self, client_id, secret):
        if secret != RPYC_SECRET:
            print(f"RPyC: Rejected connection from {client_id} - invalid secret")
            return (False, 'Invalid secret')
        
        self._client_id = client_id
        
        with _clients_lock:
            _connected_clients[client_id] = {
                'service': self,
                'connected_at': time.time()
            }
        
        print(f"RPyC: Client '{client_id}' registered successfully")
        return (True, client_id)
    
    def exposed_execute_code(self, code, timeout=60):
        if not hasattr(self, '_client_id'):
            return (False, 'Not registered', None, None, None)
        
        client_id = self._client_id
        
        stdout_capture = sys.stdout
        stderr_capture = sys.stderr
        import io
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        sys.stdout = stdout_buffer
        sys.stderr = stderr_buffer
        
        local_vars = {}
        
        try:
            exec_globals = {
                '__name__': '__rpyc_remote__',
                '__builtins__': __builtins__,
            }
            
            exec(code, exec_globals, local_vars)
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()
            
            if stderr_output:
                output += '\n[stderr]\n' + stderr_output
            
            result_repr = None
            if local_vars:
                last_value = list(local_vars.values())[-1]
                try:
                    result_repr = repr(last_value)
                except:
                    result_repr = str(last_value)
            
            return (True, result_repr, output, None, time.time())
            
        except SyntaxError as e:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            return (False, None, stdout_buffer.getvalue(), f'SyntaxError: {e.msg} (line {e.lineno})', time.time())
            
        except Exception as e:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            import traceback
            tb = traceback.format_exception(type(e), e, e.__traceback__)
            return (False, None, stdout_buffer.getvalue(), ''.join(tb), time.time())
    
    def exposed_get_system_info(self):
        if not hasattr(self, '_client_id'):
            return (None, 'Not registered')
        
        import platform
        return (self._client_id, {
            'platform': sys.platform,
            'python_version': sys.version,
            'hostname': os.environ.get('HOSTNAME', 'unknown'),
            'cwd': os.getcwd(),
            'architecture': platform.architecture(),
            'machine': platform.machine(),
            'processor': platform.processor()
        })
    
    def exposed_eval_expression(self, expr):
        if not hasattr(self, '_client_id'):
            return (False, 'Not registered')
        
        try:
            result = eval(expr, {"__builtins__": __builtins__}, {})
            return (True, repr(result))
        except Exception as e:
            return (False, str(e))
    
    def on_disconnect(self, conn):
        if hasattr(self, '_client_id'):
            with _clients_lock:
                if self._client_id in _connected_clients:
                    del _connected_clients[self._client_id]
            print(f"RPyC: Client '{self._client_id}' disconnected")


_rpyc_server = None
_rpyc_thread = None


def start_rpyc_server(port=RPYC_PORT):
    global _rpyc_server
    
    from rpyc.utils.server import ThreadedServer
    
    _rpyc_server = ThreadedServer(
        ClientRegistryService,
        port=port,
        listener_timeout=300
    )
    
    print(f"RPyC: Starting server on port {port}")
    _rpyc_server.start()


def stop_rpyc_server():
    global _rpyc_server, _rpyc_thread
    
    if _rpyc_server:
        print("RPyC: Stopping server")
        _rpyc_server.close()
        _rpyc_server = None
    
    if _rpyc_thread and _rpyc_thread.is_alive():
        _rpyc_thread.join(timeout=5)
        _rpyc_thread = None


def setup_rpyc_server():
    global _rpyc_thread
    
    _rpyc_thread = threading.Thread(target=start_rpyc_server, daemon=True)
    _rpyc_thread.start()
    
    print(f"RPyC: Server configured on port {RPYC_PORT}")


def execute_code_on_client(client_id, code, timeout=60):
    with _clients_lock:
        if client_id not in _connected_clients:
            return {'success': False, 'error': 'Client not connected', 'client_id': client_id}
        
        client_data = _connected_clients[client_id]
        service = client_data.get('service')
    
    if not service:
        return {'success': False, 'error': 'Client service not found', 'client_id': client_id}
    
    try:
        result = service.exposed_execute_code(code, timeout)
        success, res, output, error, timestamp = result
        return {
            'success': success,
            'result': res,
            'output': output,
            'error': error,
            'timestamp': timestamp,
            'client_id': client_id
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'client_id': client_id}


def get_client_system_info(client_id):
    with _clients_lock:
        if client_id not in _connected_clients:
            return {'error': 'Client not connected', 'client_id': client_id}
        
        client_data = _connected_clients[client_id]
        service = client_data.get('service')
    
    if not service:
        return {'error': 'Client service not found', 'client_id': client_id}
    
    try:
        return service.exposed_get_system_info()
    except Exception as e:
        return {'error': str(e), 'client_id': client_id}


def get_connected_clients():
    with _clients_lock:
        return {
            client_id: {
                'connected_at': data.get('connected_at')
            }
            for client_id, data in _connected_clients.items()
        }


def is_client_connected(client_id):
    with _clients_lock:
        return client_id in _connected_clients
