import base64

from flask_socketio import emit
from flask import request
from server.authorization import authorized_for_socket_io


class SocketIOServerHandler:
    def __init__(self, database):
        self.database = database

    def receive_screenshot(self,screenshot):
        if authorized_for_socket_io(request.sid, self.database):
            file_bytes = screenshot
            encoded_string = base64.b64encode(file_bytes).decode("utf-8")  # Convert to base64
            self.database.update_last_screenshot(request.sid, encoded_string)
            self.emit_screenshot_stream_for(request.sid)
        else:
            # if the client is not authorized it should not be connected anymore so we raise an exception
            raise ConnectionRefusedError()
    def request_clients(self):
        # Verify authentication status
        if authorized_for_socket_io(request.sid, self.database):
            emit('update_clients', self.database.get_payload_list())
        else:
            # if the client is not authorized it should not be connected anymore so we raise an exception
            raise ConnectionRefusedError()

    def new_connection(self, auth):
        # Verify the password from client
        client_password = auth.get('password')
        if auth.get("payload"):
            ret = authorized_for_socket_io(request.sid, self.database, password=client_password, payload=True)
            emit('update_clients', self.database.get_payload_list(), broadcast=True) # notifies everybody about updated clients
            return ret
        emit('update_clients', self.database.get_payload_list())
        return authorized_for_socket_io(request.sid, self.database, password=client_password)

    def disconnect_client(self):
        print("Client with id " + request.sid + " disconnected. Popping it from authorized clients")
        # Remove the client from the database
        try:
            self.database.get_authorized_socketio_clients().pop(request.sid)
            self.database.get_payload_list().remove(request.sid)
        except KeyError:
            print("KeyError when popping client, he disconnected but wasnt in the authorized database?!")

    def start_live_stream(self, of_paylod_sid):
        self.database.add_livestream(of_paylod_sid, request.sid)

    def stop_live_stream(self, of_payload_sid):
        self.database.remove_livestream(of_payload_sid, request.sid)

    def emit_screenshot_stream_for(self, payload_sid):
        livestreams = self.database.get_livestreams()
        if payload_sid in livestreams.keys():
            livestreams = livestreams[payload_sid]
            for browser_sid in livestreams:
                #print("Emitting newest image, but only to the clients who requested it")
                emit('newest_image_returned', {'data': self.database.get_last_screenshot(payload_sid)}, to=browser_sid)