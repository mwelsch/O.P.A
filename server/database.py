from werkzeug.security import generate_password_hash


class PseudoDatabase:
    def __init__(self):
        #self.last_screenshot = None
        self.screenshot_database = {}
        self.authorized_socketio_clients = {}
        self.socketio_hashed_passwords = [generate_password_hash('1234')]
        self.rest_api_keys = []

    def update_last_screenshot(self, device_id, file):
        self.screenshot_database[device_id] = file

    def get_last_screenshot(self, device_id):
        return self.screenshot_database[device_id]

    def get_authorized_socketio_clients(self):
        return self.authorized_socketio_clients

    def add_authorized_socketio_client(self, sid, password_hash):
        self.authorized_socketio_clients[sid] = password_hash

    def get_socketio_hashed_passwords(self):
        return self.socketio_hashed_passwords

    def get_rest_api_keys(self):
        return self.rest_api_keys

    def add_authorized_socketio_client(self):
        pass