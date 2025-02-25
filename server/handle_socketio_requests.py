from flask_socketio import emit
from flask import request
from server.authorization import authorized_for_socket_io


class SocketIOServerHandler:
    def __init__(self, database):
        self.database = database

    def stream_newest_image(self):
        print("streaming_newest_image")
        emit('newest_image_returned', {'data': self.database.get_last_screenshot()})

    def request_clients(self):
        # Verify authentication status
        if authorized_for_socket_io(request.sid, self.database):
            dummy_clients = ['Client 1', 'Client 2', 'Client 3', 'Client 4']
            emit('update_clients', dummy_clients)
        else:
            # if the client is not authorized it should not be connected anymore so we raise an exception
            raise ConnectionRefusedError()

    def new_connection(self, auth):
        # Verify the password from client
        client_password = auth.get('password')
        print(client_password)
        return authorized_for_socket_io(request.sid, self.database, password=client_password)

    def disconnect_client(self):
        print("Client with id " + request.sid + " disconnected. Popping it from authorized clients")
        # Remove the client from the database
        self.database.get_authorized_socketio_clients().pop(request.sid)

