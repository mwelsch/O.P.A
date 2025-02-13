#!/bin/python3
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit

from server.handle_server_requests import ServerHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
handler = ServerHandler()
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

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    socketio.run(app=app, debug=True, port=5000, allow_unsafe_werkzeug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
