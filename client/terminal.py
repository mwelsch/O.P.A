import os
import sys
import subprocess
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import signal

MAX_OUTPUT_SIZE = 5 * 1024 * 1024  # 5MB

if sys.platform == 'win32':
    DEFAULT_SHELL = 'cmd'
    AVAILABLE_SHELLS = {
        'cmd': ['cmd.exe', '/c'],
        'powershell': ['powershell.exe', '-Command']
    }
else:
    DEFAULT_SHELL = 'bash'
    AVAILABLE_SHELLS = {
        'bash': ['/bin/bash', '-c'],
        'sh': ['/bin/sh', '-c']
    }

command_executor = ThreadPoolExecutor(max_workers=1)
running_commands = {}

def get_platform_info():
    return {
        'platform': sys.platform,
        'default_shell': DEFAULT_SHELL,
        'available_shells': list(AVAILABLE_SHELLS.keys())
    }

def execute_command(command, shell=None, req_id=None, sio=None, webui_sid=None):
    shell = shell or DEFAULT_SHELL
    
    if shell not in AVAILABLE_SHELLS:
        return {
            'error': f'Shell "{shell}" not available. Available: {list(AVAILABLE_SHELLS.keys())}',
            'exit_code': -1
        }
    
    shell_cmd = AVAILABLE_SHELLS[shell]
    full_cmd = shell_cmd + [command]
    
    try:
        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'stdin': subprocess.DEVNULL,
            'text': True
        }
        
        if sys.platform != 'win32':
            kwargs['start_new_session'] = True
        
        proc = subprocess.Popen(full_cmd, **kwargs)
        
        running_commands[req_id] = {
            'process': proc,
            'command': command,
            'shell': shell,
            'start_time': time.time()
        }
        
        print(f"DEBUG terminal: [{time.time()}] Started command, req_id={req_id}, pid={proc.pid}")
        
        def run_in_thread():
            try:
                stdout, stderr = proc.communicate(timeout=300)
                
                combined_output = stdout or ''
                if stderr:
                    combined_output += '\n[stderr]\n' + stderr
                
                if len(combined_output) > MAX_OUTPUT_SIZE:
                    combined_output = combined_output[:MAX_OUTPUT_SIZE] + '\n... (output truncated, exceeded 5MB)'
                
                result = {
                    'output': combined_output,
                    'exit_code': proc.returncode,
                    'req_id': req_id
                }
                if webui_sid:
                    result['webui_sid'] = webui_sid
                
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                result = {
                    'error': 'Command timed out after 300 seconds',
                    'exit_code': -1,
                    'req_id': req_id
                }
                if webui_sid:
                    result['webui_sid'] = webui_sid
            except Exception as e:
                proc.kill()
                result = {
                    'error': str(e),
                    'exit_code': -1,
                    'req_id': req_id
                }
                if webui_sid:
                    result['webui_sid'] = webui_sid
            finally:
                if req_id in running_commands:
                    del running_commands[req_id]
            
            print(f"DEBUG terminal: [{time.time()}] Command completed, req_id={req_id}, exit_code={result.get('exit_code')}")
            
            if sio:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(sio.emit('command_output', result))
                finally:
                    loop.close()
        
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
        
        return {
            'running': True,
            'pid': proc.pid,
            'message': f'Command started (pid: {proc.pid})',
            'req_id': req_id
        }
        
    except Exception as e:
        print(f"DEBUG terminal: [{time.time()}] ERROR starting command: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'exit_code': -1,
            'req_id': req_id
        }

def detach_command(req_id, webui_sid=None):
    if req_id not in running_commands:
        return {
            'detached': False,
            'error': 'No running command with this ID',
            'req_id': req_id
        }
    
    proc_info = running_commands[req_id]
    proc = proc_info['process']
    
    try:
        proc.terminate()
        time.sleep(0.5)
        if proc.poll() is None:
            proc.kill()
        
        if req_id in running_commands:
            del running_commands[req_id]
        
        print(f"DEBUG terminal: [{time.time()}] Detached command, req_id={req_id}")
        
        return {
            'detached': True,
            'message': 'Command detached (terminated)',
            'req_id': req_id,
            'webui_sid': webui_sid
        }
    except Exception as e:
        return {
            'detached': False,
            'error': str(e),
            'req_id': req_id,
            'webui_sid': webui_sid
        }

def kill_command(req_id, webui_sid=None):
    if req_id not in running_commands:
        return {
            'killed': False,
            'error': 'No running command with this ID',
            'req_id': req_id
        }
    
    proc_info = running_commands[req_id]
    proc = proc_info['process']
    
    try:
        proc.kill()
        
        if req_id in running_commands:
            del running_commands[req_id]
        
        print(f"DEBUG terminal: [{time.time()}] Killed command, req_id={req_id}")
        
        return {
            'killed': True,
            'message': 'Command killed',
            'req_id': req_id,
            'webui_sid': webui_sid
        }
    except Exception as e:
        return {
            'killed': False,
            'error': str(e),
            'req_id': req_id,
            'webui_sid': webui_sid
        }

def kill_all_commands(webui_sid=None):
    killed_count = 0
    for req_id, proc_info in list(running_commands.items()):
        proc = proc_info['process']
        try:
            proc.kill()
            killed_count += 1
        except Exception as e:
            print(f"DEBUG terminal: [{time.time()}] Error killing process {req_id}: {e}")
    
    running_commands.clear()
    print(f"DEBUG terminal: [{time.time()}] Killed {killed_count} commands")
    
    return {
        'all_killed': True,
        'message': f'Killed {killed_count} command(s)',
        'webui_sid': webui_sid
    }

def setup_terminal_handlers(sio):
    @sio.on('execute_command')
    async def on_execute_command(data):
        print(f"DEBUG terminal: [{time.time()}] Received execute_command: {data.get('command', '')[:50]}...")
        
        try:
            command = data.get('command', '')
            shell = data.get('shell')
            req_id = data.get('req_id')
            webui_sid = data.get('webui_sid')
            
            print(f"DEBUG terminal: [{time.time()}] Starting command in background thread, req_id={req_id}")
            result = execute_command(command, shell, req_id, sio, webui_sid)
            
            if not result.get('running'):
                result['req_id'] = req_id
                if webui_sid:
                    result['webui_sid'] = webui_sid
                await sio.emit('command_output', result)
            
        except Exception as e:
            print(f"DEBUG terminal: [{time.time()}] ERROR in on_execute_command: {e}")
            import traceback
            traceback.print_exc()
            await sio.emit('command_output', {
                'error': str(e),
                'exit_code': -1,
                'req_id': data.get('req_id'),
                'webui_sid': data.get('webui_sid')
            })
    
    @sio.on('detach_command')
    async def on_detach_command(data):
        print(f"DEBUG terminal: [{time.time()}] Received detach_command: {data}")
        
        try:
            req_id = data.get('req_id')
            webui_sid = data.get('webui_sid')
            
            result = detach_command(req_id, webui_sid)
            
            print(f"DEBUG terminal: [{time.time()}] Sending detach response: {result}")
            await sio.emit('command_output', result)
            
        except Exception as e:
            print(f"DEBUG terminal: [{time.time()}] ERROR in on_detach_command: {e}")
            import traceback
            traceback.print_exc()
            await sio.emit('command_output', {
                'error': str(e),
                'req_id': data.get('req_id'),
                'webui_sid': data.get('webui_sid')
            })
    
    @sio.on('kill_command')
    async def on_kill_command(data):
        print(f"DEBUG terminal: [{time.time()}] Received kill_command: {data}")
        
        try:
            req_id = data.get('req_id')
            webui_sid = data.get('webui_sid')
            
            result = kill_command(req_id, webui_sid)
            
            print(f"DEBUG terminal: [{time.time()}] Sending kill response: {result}")
            await sio.emit('command_output', result)
            
        except Exception as e:
            print(f"DEBUG terminal: [{time.time()}] ERROR in on_kill_command: {e}")
            import traceback
            traceback.print_exc()
            await sio.emit('command_output', {
                'error': str(e),
                'req_id': data.get('req_id'),
                'webui_sid': data.get('webui_sid')
            })
    
    @sio.on('kill_all_commands')
    async def on_kill_all_commands(data):
        print(f"DEBUG terminal: [{time.time()}] Received kill_all_commands: {data}")
        
        try:
            webui_sid = data.get('webui_sid')
            
            result = kill_all_commands(webui_sid)
            
            print(f"DEBUG terminal: [{time.time()}] Sending kill all response: {result}")
            await sio.emit('command_output', result)
            
        except Exception as e:
            print(f"DEBUG terminal: [{time.time()}] ERROR in on_kill_all_commands: {e}")
            import traceback
            traceback.print_exc()
            await sio.emit('command_output', {
                'error': str(e),
                'webui_sid': data.get('webui_sid')
            })
    
    @sio.on('get_platform_info')
    async def on_get_platform_info(data):
        print(f"DEBUG terminal: [{time.time()}] Received get_platform_info request")
        
        try:
            req_id = data.get('req_id')
            webui_sid = data.get('webui_sid')
            
            info = get_platform_info()
            info['req_id'] = req_id
            if webui_sid:
                info['webui_sid'] = webui_sid
            
            print(f"DEBUG terminal: [{time.time()}] Sending platform info: {info}")
            await sio.emit('platform_info', info)
            print(f"DEBUG terminal: [{time.time()}] Platform info sent successfully")
        except Exception as e:
            print(f"DEBUG terminal: [{time.time()}] ERROR in on_get_platform_info: {e}")
            import traceback
            traceback.print_exc()
