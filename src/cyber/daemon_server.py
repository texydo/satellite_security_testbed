import socket
import threading
import subprocess
from client.utils import receive_msgpack
import configparser


def handle_client(connection):
    with connection:
        print('Connected by', connection.getpeername())
        componentFileName = "main.py"
        while True:
            data = receive_msgpack(connection)
            print(data)
            if not data:
                break
            subprocess.Popen(["python", componentFileName, data[1]], shell=True)

def start_daemon():
    config = configparser.ConfigParser()
    config.read('../cyber_config.ini')
        
    HOST=config.get('DAEMON_SERVER', 'HOST')
    PORT=config.getint('DAEMON_SERVER', 'PORT')
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn,)).start()

if __name__ == "__main__":
    start_daemon()
