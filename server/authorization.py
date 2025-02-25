from flask_socketio import emit, disconnect
from werkzeug.security import check_password_hash

from server.database import PseudoDatabase


def authorized_for_socket_io(sid, database: PseudoDatabase, password=None):
    # If a password is provided check it against hashed passwords
    # If succeeded the client will be added to the list of authorized clients
    if password:
        for saved_password in database.get_socketio_hashed_passwords():
            if check_password_hash(password, saved_password):
                database.add_authorized_socketio_client(sid, saved_password)
                return True
        return False
    authorized_clients = database.get_authorized_socketio_clients()
    if authorized_clients[sid] is None:
        emit('error', {'message': 'Not authenticated'})
        disconnect()
        return False
    else:
        return True

def authorized_for_rest():
    print("Hi!")