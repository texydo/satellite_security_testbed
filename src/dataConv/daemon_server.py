import socket
import threading
import subprocess
from utils import receive_msgpack
import sys
import configparser
import requests; connected = False

config=configparser.ConfigParser()
config.read('dataConv_config.ini')

HOST=config.get('DAEMON_SERVER', 'daemon_IP') 
PORT=config.getint('DAEMON_SERVER', 'daemon_PORT')
try: connected = requests.get("https://www.google.com", timeout=3).ok
except: pass

def handle_client(connection):
    with connection:
        print('Connected by', connection.getpeername())
        # componentFileName = r"C:\Users\SatUser\Desktop\ENV_stub\OrbitalComputer\OrbitalSTUB.py"
        componentFileName = "dataConvManager.py"
        
        
        while True:
            data = receive_msgpack(connection)
            print("me", data)
            if not data:
                break
                
            print("manager run")   
            subprocess.Popen(["python", componentFileName, data[1],str(connected)], shell=True)

def start_daemon():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn,)).start()

if __name__ == "__main__":
    start_daemon()
