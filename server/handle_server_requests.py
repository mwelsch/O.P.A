import asyncio
import base64
from flask import render_template
from flask_socketio import emit

from server.database import PseudoDatabase


class ServerHandler:
    def __init__(self):
        self.database = PseudoDatabase()
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

        #return send_file(BytesIO(self.database.get_last_screenshot()),
        #         download_name="Renamed.jpg", as_attachment=True)

        return render_template('control.html', user_image = self.database.get_last_screenshot())

    def stream_newest_image(self):
        print("streaming_newest_image")
        print(self.database.get_last_screenshot())
        print(type(self.database.get_last_screenshot()))
        emit('newest_image_returned', {'data': self.database.get_last_screenshot()})


