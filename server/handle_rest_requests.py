import asyncio
import base64
from flask import render_template
from flask_socketio import emit

from server.database import PseudoDatabase

class RESTServerHandler:
    def __init__(self, database):
        self.database = database

    def screenshot_received(self, request):
        if request.method == 'POST':
            api_key = request.headers.get("Authorization")
            device_id = request.headers.get("Device-ID")
            print(api_key)
            print(device_id)
            file = request.files['file']
            file.seek(0)
            file_bytes = file.read()  # Read file as binary
            encoded_string = base64.b64encode(file_bytes).decode("utf-8")  # Convert to base64
            self.database.update_last_screenshot(device_id, encoded_string)
            return f'Uploaded'
        return render_template('index.html')

    def control_view(self):
        pass




