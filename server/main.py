#!/bin/python3
from time import sleep

from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit, disconnect
from werkzeug.security import generate_password_hash, check_password_hash

from server.database import PseudoDatabase
from server.handle_rest_requests import RESTServerHandler
from server.handle_socketio_requests import SocketIOServerHandler
from server.register_handlers import register_http_handlers, register_socket_io_handlers
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
socketio = SocketIO(app)
database = PseudoDatabase()
rest_handler = RESTServerHandler(database)
socketio_handler = SocketIOServerHandler(database)
register_http_handlers(app, rest_handler)
register_socket_io_handlers(socketio, socketio_handler)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    socketio.run(app=app, debug=True, port=5000, allow_unsafe_werkzeug=True)

