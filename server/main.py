#!/bin/python3
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit, disconnect
from werkzeug.security import generate_password_hash, check_password_hash

from server.handle_server_requests import ServerHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
hashed_password = generate_password_hash(app.config['SECRET_KEY'])
socketio = SocketIO(app)
handler = ServerHandler()
authorized_clients = {}
@app.route('/', methods=['GET', 'POST'])
def receive_screenshot():
    return handler.screenshot_received(request)

@app.route('/control', methods=['GET', 'POST'])
def show_screen():
    return handler.control_view()

@app.route('/live_stream', methods=['GET', 'POST'])
def live_stream():
    return render_template('live_screen_stream.html')

@socketio.on('get_newest_image')
def get_newest_image():
    handler.stream_newest_image()

@socketio.on('request_clients')
def requesting_clients():
    # Verify authentication status
    if not authorized_clients.get(request.sid, {}).get('authenticated'):
        emit('error', {'message': 'Not authenticated'})
        disconnect()
        return
    dummy_clients = ['Client 1', 'Client 2', 'Client 3', 'Client 4']
    emit('update_clients', dummy_clients)

@socketio.on('connect')
def handle_connect(auth):
    try:
        # Verify the password from client
        client_password = auth.get('password')
        print(client_password)
        if not client_password:
            raise ConnectionRefusedError('No password provided')
        if not check_password_hash(hashed_password, client_password):
            raise ConnectionRefusedError('Password hashes do not seem to match...')
        # Store valid connection (optional)
        authorized_clients[request.sid] = {
            'authenticated': True,
            'password': client_password
        }
        print(authorized_clients)
    except Exception as e:
        print(f"Rejected connection: {str(e)}")
        disconnect()
        return False
    #my_check_password(request)




@socketio.on('disconnect')
def test_disconnect():
    # Clean up connection record
    authorized_clients.pop(request.sid, None)
    print('Client disconnected')

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    socketio.run(app=app, debug=True, port=5000, allow_unsafe_werkzeug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
