from flask_socketio import emit, disconnect
from werkzeug.security import check_password_hash

from server.database import PseudoDatabase


def authorized_for_socket_io(sid, database, password=None, payload=False):
    # If a password is provided check it against hashed passwords
    # If succeeded the client will be added to the list of authorized clients
    if password:
        for saved_password in database.get_socketio_hashed_passwords():
            if check_password_hash(saved_password, password):
                database.add_authorized_socketio_client(sid, saved_password)
                if payload:
                    database.add_payload_client(sid)
                return True
        return False
    authorized_clients = database.get_authorized_socketio_clients()
    if not sid in authorized_clients.keys():
        emit('error', {'message': 'Not authenticated'})
        disconnect()
        return False
    else:
        return True

def authorized_for_rest():
    print("Hi!")