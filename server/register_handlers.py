from flask import request, render_template


def register_socket_io_handlers(socketio, socketio_handler):
    @socketio.on('get_newest_image')
    def get_newest_image():
        socketio_handler.stream_newest_image()

    @socketio.on('request_clients')
    def requesting_clients():
        socketio_handler.reqest_clients()

    @socketio.on('connect')
    def handle_connect(auth):
        if not socketio_handler.new_connection(auth):
            return False

    @socketio.on('disconnect')
    def test_disconnect():
        socketio_handler.disconnect_client()

def register_http_handlers(app, rest_handler):
    @app.route('/', methods=['POST'])
    def receive_screenshot():
        return rest_handler.screenshot_received(request)

    @app.route('/control', methods=['GET', 'POST'])
    def show_screen():
        return render_template('control.html')
        #return rest_handler.control_view()

    @app.route('/live_stream', methods=['GET', 'POST'])
    def live_stream():
        return render_template('live_screen_stream.html')