from time import sleep

import server_communication

def read_config():
    print("Reading config")

print("HIHIHI")
if __name__ == '__main__':
    print("HIHIHI")
    #ToDo read_config()
    server = server_communication.Server("http://127.0.0.1:5000")


    while server.running() is True:
        print("HIHIHI")
        sleep(3600) #one hour

